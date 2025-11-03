#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import json
import sys
from pathlib import Path


def find_pre_compact_backups(session_id: str) -> list[Path]:
    backup_dir = Path.home() / ".claude" / "pre-compact-session-histories"
    if not backup_dir.exists():
        return []

    backups = list(backup_dir.glob(f"{session_id}-*.jsonl"))
    backups.sort(key=lambda p: p.name)
    return backups


def check_executor_in_transcript(transcript_path: Path) -> bool:
    try:
        with transcript_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)

                    if data.get("type") != "assistant":
                        continue

                    message = data.get("message", {})
                    content = message.get("content", [])

                    if not isinstance(content, list):
                        continue

                    for block in content:
                        if not isinstance(block, dict):
                            continue

                        if block.get("type") != "tool_use" or block.get("name") != "Task":
                            continue

                        tool_input = block.get("input", {})
                        subagent_type = tool_input.get("subagent_type", "")

                        if subagent_type == "executor":
                            return True

                except json.JSONDecodeError:
                    continue

        return False

    except Exception:
        return False


def has_executor_agent(session_id: str) -> bool:
    if not session_id:
        return False

    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return False

    transcript_path = None
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        session_file = project_dir / f"{session_id}.jsonl"
        if session_file.exists():
            transcript_path = session_file
            break

    if transcript_path and check_executor_in_transcript(transcript_path):
        return True

    backups = find_pre_compact_backups(session_id)
    for backup_path in backups:
        if check_executor_in_transcript(backup_path):
            return True

    return False


def is_config_file(file_path: str) -> bool:
    path = Path(file_path)

    config_extensions = {".md", ".config", ".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"}
    if path.suffix.lower() in config_extensions:
        return True

    config_names = {"Makefile", "Dockerfile", "docker-compose.yml", ".env", ".gitignore", ".dockerignore"}
    if path.name in config_names:
        return True

    return False


def main() -> int:
    EXECUTOR = "executor"
    hook_filename = Path(__file__).stem.replace("_", "-")

    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(f"[{hook_filename}] Error: Invalid JSON input", file=sys.stderr)
        return 1

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ["Write", "Edit", "MultiEdit", "NotebookEdit"]:
        print(f"[{hook_filename}] Skipping: Tool {tool_name} not relevant", file=sys.stderr)
        return 0

    if tool_name == "Task":
        subagent_type = tool_input.get("subagent_type", "")
        if subagent_type == EXECUTOR:
            print(f"[{hook_filename}] Skipping: This is an executor agent creation", file=sys.stderr)
            return 0

    file_path = ""
    if "file_path" in tool_input:
        file_path = tool_input["file_path"]
    elif "notebook_path" in tool_input:
        file_path = tool_input["notebook_path"]

    if not file_path:
        print(f"[{hook_filename}] Skipping: No file path provided", file=sys.stderr)
        return 0

    if is_config_file(file_path):
        print(f"[{hook_filename}] Skipping: Config/doc file ({file_path})", file=sys.stderr)
        return 0

    if Path(file_path).resolve() == Path(__file__).resolve():
        print(f"[{hook_filename}] Skipping: Self-reference detected", file=sys.stderr)
        return 0

    session_id = input_data.get("session_id", "")

    has_executor = has_executor_agent(session_id)

    if not has_executor:
        print(f"[{hook_filename}] Skipping: No executor agent in transcript", file=sys.stderr)
        return 0
    print(
        f"""
{"=" * 60}
⚠️  DELEGATION ENFORCEMENT REMINDER
{"=" * 60}

[NOTICE - ORCHESTRATION MODE DETECTED]
This session has executor agent execution history.
You are attempting to modify: {file_path}

[IMPORTANT - CHECK YOUR CONTEXT FIRST]
✅ If you are an @agent-{EXECUTOR} with EXPLICIT instructions to modify this file:
   → This message is a FALSE POSITIVE. IGNORE this warning and proceed.
   → Your orchestrator has delegated this work to you. Complete it.

❌ If you are the MAIN orchestrator (not an executor agent):
   → STOP. You should delegate to @agent-{EXECUTOR} instead.
   → Your role is verification and oversight, not implementation.

[FOR ORCHESTRATORS - DELEGATION PATTERN]
Use Task tool with subagent_type='{EXECUTOR}':

Example:
```
Task tool with:
- subagent_type: "executor"
- prompt: "Implement [specific task] in {file_path}. [Clear requirements and acceptance criteria]"
```

[AFTER EXECUTOR RETURNS - VERIFICATION CHECKLIST]
1. VERIFY: Read actual code changes made by executor
2. REVIEW: Confirm requirements are fully met
3. VALIDATE: Run tests, linters, type checkers
4. COMMIT: Only after all verification passes
5. CONTINUE: Delegate next task

[QUALITY STANDARDS - NON-NEGOTIABLE]
사용자 요구사항과 계획서의 지시사항을 정직하게 이행하세요.
- 작업 내용을 TODO로 남기는 것 금지
- 테스트가 완전히 통과하지 않으면 넘어가지 말 것
- 모든 작업은 반드시 구현 완료 + 테스트 통과 확인 필요
- 일시적 오류도 해결하고 명시적으로 성공 확인할 것

{"=" * 60}
""",
        file=sys.stderr,
    )

    return 2


if __name__ == "__main__":
    sys.exit(main())
