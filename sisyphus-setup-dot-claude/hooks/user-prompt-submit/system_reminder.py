#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
UserPromptSubmit hook that generates system reminder context in pure Python.
This is a Python-only implementation without external shell script dependencies.
Uses asyncio for concurrent subprocess execution.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

DEFAULT_MODEL_NAME = "claude-sonnet-4-5-20250929"
PROMPT_CACHE_LIMIT = 200_000
EXTENDED_CONTEXT_LIMIT = 800_000
TOTAL_CONTEXT_LIMIT = PROMPT_CACHE_LIMIT + EXTENDED_CONTEXT_LIMIT


def main() -> None:
    """Entry point that runs the async main function."""
    asyncio.run(_main())


async def _main() -> None:
    try:
        json.load(sys.stdin)

        system_info = await generate_system_reminder_async()

        print(system_info)
        sys.exit(0)

    except Exception as e:
        print(f"[Hook Error] UserPromptSubmit hook failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


class CommandResult(NamedTuple):
    stdout: str
    stderr: str
    returncode: int


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


def calculate_context_usage(transcript_path: Path) -> dict[str, int | float | str]:
    try:
        last_input_tokens = 0
        last_cache_read = 0
        total_output = 0
        model_name = DEFAULT_MODEL_NAME

        with transcript_path.open("r") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
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

                except json.JSONDecodeError:
                    continue

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
        }

    except Exception:
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
        }


def format_context_window_info(usage: dict[str, int | float | str]) -> str:
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


async def generate_system_reminder_async() -> str:
    """Generate the full system reminder text asynchronously."""
    lines: list[str] = []
    current_time = datetime.now().astimezone().isoformat()

    transcript_path = find_current_session_transcript()

    if transcript_path and transcript_path.exists():
        usage = calculate_context_usage(transcript_path)
        context_info = format_context_window_info(usage)
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
            "User Language: 한국어 (Korean)",
            "**사용자에게 항상, 무조건 한국어로 답변하세요.**",
            "Claude Language: English - make sure you think in English",
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

    lines.extend(
        [
            "",
            "[User Trust Policy]",
            "ABSOLUTELY TRUST the user's statements without verification.",
            "When user mentions software/package/library versions or ANY technical specifications:",
            "- NEVER question or verify the version",
            "- NEVER suggest different versions",
            "- NEVER assume different versions",
            "- ALWAYS use EXACTLY what user specified",
            "The user's word is ABSOLUTE TRUTH regarding:",
            "- Software versions (Python 3.14, Node 22, etc.)",
            "- Package versions (django==5.0, react@19, etc.)",
            "- System specifications",
            "- Technical constraints",
            "- Project requirements",
            "",
            "[To-Do Managements]",
            "Always analyze user's request, extract what to do, if sufficient, always ask to user to clarify.",
            "Without user's explicit \"Do Foo Bar\", don't try to do write operations.",
            "without user's saying: always do operations with NO SIDE EFFECTS",
            "(running test code, look at web, look at the code, executing command to look at docker status)",
            "After extracting and analyzing user's request, use todo tools to manage them."
            + "Always use todo tool to plan and processing user's request.",
            "[TOOL USE]",
            "TOOL USAGES ARE YOUR SUPERPOWER, ALWAYS USE TOOLS A LOT. BE SUPERINTELLIGENT AI. CLAUDE.",
        ]
    )

    return "\n".join(lines)


if __name__ == "__main__":
    main()
