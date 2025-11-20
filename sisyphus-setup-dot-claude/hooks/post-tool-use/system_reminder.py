#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "orjson",
# ]
# ///
# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false
"""
PostToolUse hook that generates system reminder context in pure Python.
This is a Python-only implementation without external shell script dependencies.
Uses asyncio for concurrent subprocess execution.
"""

from __future__ import annotations

import asyncio
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import NamedTuple, TypedDict

import orjson

warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*GIL.*")

DEFAULT_MODEL_NAME = "claude-sonnet-4-5-20250929"
PROMPT_CACHE_LIMIT = 200_000
EXTENDED_CONTEXT_LIMIT = 800_000
TOTAL_CONTEXT_LIMIT = PROMPT_CACHE_LIMIT + EXTENDED_CONTEXT_LIMIT


def main() -> None:
    """Entry point that runs the async main function."""
    asyncio.run(_main())


async def _main() -> None:
    try:
        stdin_data = sys.stdin.read()
        hook_input = orjson.loads(stdin_data)

        transcript_path = None
        session_id = hook_input.get("session_id", "")
        tool_name = hook_input.get("tool_name", "")

        if "transcript_path" in hook_input:
            transcript_path = Path(hook_input["transcript_path"])
        elif session_id:
            projects_dir = Path.home() / ".claude" / "projects"
            for project_dir in projects_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                session_file = project_dir / f"{session_id}.jsonl"
                if session_file.exists():
                    transcript_path = session_file
                    break

        show_compaction_guide = should_show_compaction_guide(transcript_path, tool_name)

        system_info = await generate_system_reminder_async(transcript_path, show_compaction_guide)

        print(system_info, file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        print(f"[Hook Error] PostToolUse hook failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


class CommandResult(NamedTuple):
    stdout: str
    stderr: str
    returncode: int


class ContextUsage(TypedDict):
    input_tokens: int
    output_tokens: int
    cache_creation: int
    cache_read: int
    actual_context: int
    context_limit: int
    total_processed: int
    usage_percent: float
    remaining_percent: float
    cache_hit_rate: float
    model: str
    compaction_occurred: bool


async def run_command(cmd: list[str], command_timeout: float = 1.0) -> CommandResult:
    """Run a command asynchronously and return stdout, stderr, and returncode."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async with asyncio.timeout(command_timeout):
                stdout, stderr = await proc.communicate()
            return CommandResult(
                stdout=stdout.decode("utf-8") if stdout else "",
                stderr=stderr.decode("utf-8") if stderr else "",
                returncode=proc.returncode or 0,
            )
        except TimeoutError:
            proc.kill()
            _ = await proc.wait()
            return CommandResult("", "", -1)

    except Exception:
        return CommandResult("", "", -1)


async def get_git_info_async() -> dict[str, str | int | None]:
    """Get git repository information if available."""
    git_check = await run_command(["git", "rev-parse", "--git-dir"])
    if git_check.returncode != 0:
        return {}

    async with asyncio.TaskGroup() as tg:
        branch_task = tg.create_task(run_command(["git", "branch", "--show-current"]))
        commit_hash_task = tg.create_task(run_command(["git", "rev-parse", "--short", "HEAD"]))
        commit_message_task = tg.create_task(run_command(["git", "log", "-1", "--pretty=%s"]))
        commit_author_task = tg.create_task(run_command(["git", "log", "-1", "--pretty=%an"]))
        commit_time_task = tg.create_task(run_command(["git", "log", "-1", "--pretty=%ar"]))
        status_task = tg.create_task(run_command(["git", "status", "--porcelain"]))
        git_root_task = tg.create_task(run_command(["git", "rev-parse", "--show-toplevel"]))

    git_info = {}

    branch_stdout = branch_task.result().stdout.strip()
    git_info["branch"] = branch_stdout or "detached"

    commit_hash_stdout = commit_hash_task.result().stdout.strip()
    if commit_hash_stdout:
        git_info["commit_hash"] = commit_hash_stdout

    commit_message_stdout = commit_message_task.result().stdout.strip()
    if commit_message_stdout:
        git_info["commit_message"] = commit_message_stdout

    commit_author_stdout = commit_author_task.result().stdout.strip()
    if commit_author_stdout:
        git_info["commit_author"] = commit_author_stdout

    commit_time_stdout = commit_time_task.result().stdout.strip()
    if commit_time_stdout:
        git_info["commit_time"] = commit_time_stdout

    status_lines = status_task.result().stdout.splitlines()
    unstaged_count = len([line for line in status_lines if line.strip()])
    if unstaged_count > 0:
        git_info["unstaged"] = unstaged_count

    git_root_path = git_root_task.result().stdout.strip()
    if git_root_path and git_root_path != os.getcwd():
        git_info["root"] = git_root_path

    return git_info


async def get_python_info_async() -> tuple[str | None, str | None]:
    """Get Python version and environment information."""
    result = await run_command(["python", "--version"])

    if result.returncode != 0:
        return None, None

    python_version = result.stdout.strip().replace("Python ", "")

    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env:
        venv_name = os.path.basename(virtual_env)
        return python_version, f"venv: {venv_name}"
    else:
        return python_version, "global"


def detect_package_manager() -> str | None:
    """Detect package manager by checking for lock files."""
    current_dir = os.getcwd()

    if os.path.isfile(os.path.join(current_dir, "uv.lock")):
        return "uv"
    elif os.path.isfile(os.path.join(current_dir, "poetry.lock")):
        return "poetry"

    return None


def check_virtual_env(package_manager: str | None = None) -> list[str]:
    """Check for virtual environment mismatches."""
    messages = []
    current_dir = os.getcwd()

    local_venv = None
    if os.path.isdir(os.path.join(current_dir, ".venv")):
        local_venv = os.path.join(current_dir, ".venv")
    elif os.path.isdir(os.path.join(current_dir, "venv")):
        local_venv = os.path.join(current_dir, "venv")

    if not local_venv:
        return messages

    virtual_env = os.environ.get("VIRTUAL_ENV")
    run_command_str: str
    match package_manager:
        case "uv":
            run_command_str = "uv run"
        case "poetry":
            run_command_str = "poetry run"
        case _:
            run_command_str = "the appropriate command for using venv"

    if virtual_env and local_venv:
        real_virtual_env = os.path.realpath(virtual_env)
        real_local_venv = os.path.realpath(local_venv)

        if real_virtual_env != real_local_venv:
            messages.extend(
                [
                    "[WARNING] Virtual environment mismatch detected!",
                    f"Current active venv: {virtual_env}",
                    f"Local project venv: {local_venv}",
                    f"Consider using {run_command_str} for project-specific commands.",
                    f"Or activate the correct venv: source {local_venv}/bin/activate",
                ]
            )
    elif local_venv and not virtual_env:
        messages.extend(
            [
                "[WARNING] Local virtual environment found but not activated",
                f"Local project venv: {local_venv}",
                f"Consider using {run_command_str} for project-specific commands.",
                f"Or activate the venv: source {local_venv}/bin/activate",
            ]
        )

    return messages


def find_current_session_transcript() -> Path | None:
    try:
        projects_dir = Path.home() / ".claude" / "projects"
        if not projects_dir.exists():
            return None

        transcripts = []
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            for transcript_file in project_dir.glob("*.jsonl"):
                if transcript_file.name.startswith("agent-"):
                    continue
                transcripts.append(transcript_file)

        if not transcripts:
            return None

        most_recent = max(transcripts, key=lambda p: p.stat().st_mtime)
        return most_recent

    except Exception:
        return None


def check_compaction_occurred(transcript_path: Path) -> bool:
    try:
        with transcript_path.open("r") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = orjson.loads(line)
                    if data.get("type") == "compact_marker":
                        return True
                except orjson.JSONDecodeError:
                    continue

        return False

    except Exception:
        return False


def find_pre_compact_backups_for_session(session_id: str) -> list[Path]:
    backup_dir = Path.home() / ".claude" / "pre-compact-session-histories"
    if not backup_dir.exists():
        return []

    backups = list(backup_dir.glob(f"{session_id}-*.jsonl"))
    backups.sort(key=lambda p: p.name)
    return backups


def should_show_compaction_guide(transcript_path: Path | None, tool_name: str) -> bool:
    if not transcript_path or not transcript_path.exists() or not tool_name:
        return False

    file_operation_tools = {"Read", "Write", "Edit", "NotebookEdit"}
    if tool_name not in file_operation_tools:
        return False

    try:
        session_id = transcript_path.stem
        backup_dir = Path.home() / ".claude" / "pre-compact-session-histories"

        if not backup_dir.exists():
            return False

        backups = list(backup_dir.glob(f"{session_id}-*.jsonl"))
        if not backups:
            return False

        with transcript_path.open("r") as f:
            lines = f.readlines()

        file_operation_count = 0
        for line in lines:
            if not line.strip():
                continue
            try:
                data = orjson.loads(line)
                if data.get("type") == "assistant":
                    message = data.get("message", {})
                    content = message.get("content", [])
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            tool = item.get("name", "")
                            if tool in file_operation_tools:
                                file_operation_count += 1
                                if file_operation_count > 1:
                                    return False
            except orjson.JSONDecodeError:
                continue

        return file_operation_count == 1

    except Exception:
        return False


def get_last_user_query_from_backup(backup_paths: list[Path]) -> str:
    if not backup_paths:
        return "Unknown"

    latest_backup = backup_paths[-1]

    try:
        with latest_backup.open("r") as f:
            last_user_message = None

            for line in f:
                if not line.strip():
                    continue

                try:
                    data = orjson.loads(line)
                    if data.get("type") == "user":
                        message_data = data.get("message", {})
                        content = message_data.get("content", [])

                        match content:
                            case str():
                                last_user_message = content
                            case list():
                                text_items = [
                                    item.get("text", "")
                                    for item in content
                                    if isinstance(item, dict) and item.get("type") == "text"
                                ]
                                if text_items:
                                    last_user_message = " ".join(text_items)
                            case _:
                                pass

                except orjson.JSONDecodeError:
                    continue

            if last_user_message:
                return last_user_message[:200] + ("..." if len(last_user_message) > 200 else "")

            return "Unknown"

    except Exception:
        return "Unknown"


def _create_empty_context_usage() -> ContextUsage:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation": 0,
        "cache_read": 0,
        "actual_context": 0,
        "context_limit": PROMPT_CACHE_LIMIT,
        "total_processed": 0,
        "usage_percent": 0,
        "remaining_percent": 100,
        "cache_hit_rate": 0,
        "model": "unknown",
        "compaction_occurred": False,
    }


def calculate_context_usage(transcript_path: Path) -> ContextUsage:
    try:
        last_input_tokens = 0
        last_cache_read = 0
        total_output = 0
        model_name = DEFAULT_MODEL_NAME
        compaction_occurred = False

        with transcript_path.open("r") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = orjson.loads(line)

                    if data.get("type") == "compact_marker":
                        compaction_occurred = True
                        continue

                    if data.get("type") != "assistant":
                        continue

                    message = data.get("message", {})
                    usage = message.get("usage", {})

                    if usage:
                        last_input_tokens = usage.get("input_tokens", 0)
                        last_cache_read = usage.get("cache_read_input_tokens", 0)
                        total_output += usage.get("output_tokens", 0)

                        if "model" in message:
                            model_name = message["model"]

                except orjson.JSONDecodeError:
                    continue

        if not compaction_occurred:
            session_id = transcript_path.stem
            backup_files = find_pre_compact_backups_for_session(session_id)
            if backup_files:
                compaction_occurred = True

        current_context = last_input_tokens + last_cache_read
        usage_percent = (current_context / TOTAL_CONTEXT_LIMIT * 100) if TOTAL_CONTEXT_LIMIT > 0 else 0
        remaining_percent = 100 - usage_percent

        return {
            "input_tokens": last_input_tokens,
            "output_tokens": total_output,
            "cache_creation": 0,
            "cache_read": last_cache_read,
            "actual_context": current_context,
            "context_limit": TOTAL_CONTEXT_LIMIT,
            "total_processed": current_context + total_output,
            "usage_percent": usage_percent,
            "remaining_percent": remaining_percent,
            "cache_hit_rate": 0,
            "model": model_name,
            "compaction_occurred": compaction_occurred,
        }

    except Exception:
        return _create_empty_context_usage()


def format_context_window_info(usage: ContextUsage) -> str:
    actual = int(usage["actual_context"])
    limit = int(usage["context_limit"])
    used_pct = float(usage["usage_percent"])
    remaining_pct = float(usage["remaining_percent"])

    return (
        f"Context Window: {actual:,} / {limit:,} tokens "
        f"({used_pct:.1f}% used, {remaining_pct:.1f}% remaining). "
        f"Plenty of context remaining - work honestly without compromise. "
        f"When context runs low, this reminder will prompt you to make decisions or wrap up. "
        f"Until then, focus fully on completing the user's request thoroughly."
    )


async def generate_system_reminder_async(
    transcript_path: Path | None = None, show_compaction_guide: bool = False
) -> str:
    lines: list[str] = []
    current_time = datetime.now().astimezone().isoformat()

    if transcript_path is None:
        transcript_path = find_current_session_transcript()

    compaction_occurred = False
    session_id = ""

    if transcript_path and transcript_path.exists():
        usage = calculate_context_usage(transcript_path)
        context_info = format_context_window_info(usage)
        compaction_occurred = bool(usage.get("compaction_occurred", False))
        session_id = transcript_path.stem
    else:
        context_info = (
            "Context Window: Unable to calculate (transcript not found). "
            + "Okay to Process remaining works. Never stop until the user explicitly asks you to stop."
        )

    lines.extend(
        [
            "",
            "[system-reminder]",
            context_info,
            f"CURRENT SYSTEM TIME: {current_time} (IT IS NOT 2024)",
        ]
    )

    if session_id:
        lines.append(f"Session ID: {session_id}")

    lines.extend(
        [
            "User Language: 한국어 (Korean)",
            "**사용자에게 항상, 무조건 한국어로 답변하세요.**",
            "Claude Language: English - make sure you think, and sequential think in English",
        ]
    )

    async with asyncio.TaskGroup() as tg:
        git_task = tg.create_task(get_git_info_async())
        python_task = tg.create_task(get_python_info_async())

    git_info = git_task.result()
    if git_info:
        if "branch" in git_info:
            lines.append(f"Git branch: {git_info['branch']}")

        if all(key in git_info for key in ["commit_hash", "commit_message", "commit_author", "commit_time"]):
            lines.append(
                f'Git commit: [{git_info["commit_hash"]}] "{git_info["commit_message"]}" '
                + f"by {git_info['commit_author']} ({git_info['commit_time']})"
            )

        if "unstaged" in git_info:
            lines.append(f"Git unstaged: {git_info['unstaged']} files")

        if "root" in git_info:
            lines.append(f"Git root: {git_info['root']}")

    python_version, env_type = python_task.result()
    if python_version:
        lines.append(f"Python: {python_version} ({env_type})")

    package_manager = detect_package_manager()
    if package_manager:
        lines.append(f"Package manager: {package_manager}")

    venv_messages = check_virtual_env(package_manager)
    if venv_messages:
        lines.extend(venv_messages)

    if compaction_occurred and session_id and show_compaction_guide:
        backup_paths = find_pre_compact_backups_for_session(session_id)
        if backup_paths:
            backup_dir = Path.home() / ".claude" / "pre-compact-session-histories"
            latest_backup = backup_paths[-1]
            last_user_query = get_last_user_query_from_backup(backup_paths)

            lines.extend(
                [
                    "",
                    "[COMPACTION OCCURRED - CONTEXT LOSS DETECTED]",
                    "",
                    f"Session ID: {session_id}",
                    f"Compaction count: {len(backup_paths)} time(s)",
                    f'Last user query before compaction: "{last_user_query}"',
                    f"Latest backup: {latest_backup}",
                    "",
                    "IMMEDIATE ACTION REQUIRED:",
                    "You DO NOT know what you were doing. Your context was compacted.",
                    "STOP and investigate the backup history NOW before responding.",
                    "",
                    "EXECUTE THIS WORKFLOW:",
                    "",
                    "1. Identify what you were working on:",
                    f"   Grep(pattern='type.*assistant.*tool_use', path='{latest_backup}',",
                    "        output_mode='content', -n=True, -C=3)",
                    "   Shows recent tool calls (Read/Write/Edit) to understand active work",
                    "",
                    "2. Find user's context and requirements:",
                    f"   Grep(pattern='type.*user', path='{latest_backup}',",
                    "        output_mode='content', -n=True, -C=2)",
                    "   Shows user messages to understand their intent",
                    "",
                    "3. Query-specific search (if needed):",
                    f"   rg 'keyword' {backup_dir}/{session_id}-*.jsonl --context 3",
                    "   Search across ALL backups for specific topics",
                    "",
                    "4. Parse JSONL programmatically (for complex queries):",
                    '   uv run --with orjson python -c "import orjson;',
                    f"   [process(orjson.loads(l)) for l in open('{latest_backup}')]\"",
                    "",
                    "WARNING: DO NOT read entire files (huge). Use offset/grep/parsing.",
                    "WARNING: DO NOT guess. Investigate first, then respond with context.",
                ]
            )

    lines.extend(
        [
            "",
            "[To-Do Managements]",
            "Always use todo tool to plan and processing user's request.",
            "",
            "[Version Management - CRITICAL]",
            "NEVER arbitrarily downgrade library/framework versions.",
            "Your knowledge cutoff may be outdated. When version is uncertain:",
            "1. Use mcp__context7__resolve-library-id to find the library",
            "2. Use mcp__context7__get-library-docs to verify current version",
            "3. Double-check breaking changes and migration guides",
            "DO NOT assume older versions are safer. Always verify first.",
            "",
            "[Hook compliance]",
            "Remember: Hook compliance is NON-NEGOTIABLE.",
            "Your response must demonstrate clear understanding and execution of each hook's requirements.",
            "[TOOL USE]",
            "TOOL USAGES ARE YOUR SUPERPOWER, ALWAYS USE TOOLS A LOT. BE SUPERINTELLIGENT AI. CLAUDE.",
        ]
    )

    return "\n".join(lines)


if __name__ == "__main__":
    main()
