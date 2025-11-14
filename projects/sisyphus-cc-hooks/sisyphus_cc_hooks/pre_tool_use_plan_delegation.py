from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NotRequired, TypedDict


class ToolInput(TypedDict):
    file_path: NotRequired[str]
    notebook_path: NotRequired[str]


class HookInput(TypedDict):
    tool_name: str
    tool_input: ToolInput
    session_id: NotRequired[str]
    cwd: NotRequired[str]


def is_sisyphus_plan_yaml(file_path: str) -> bool:
    if not file_path:
        return False

    path = Path(file_path)

    if path.suffix not in [".yaml", ".yml"]:
        return False

    parts = path.parts
    try:
        sisyphus_idx = parts.index(".sisyphus")
        if sisyphus_idx + 1 < len(parts) and parts[sisyphus_idx + 1] == "tasks":
            return True
    except (ValueError, IndexError):
        pass

    return False


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

                        if (
                            block.get("type") != "tool_use"
                            or block.get("name") != "Task"
                        ):
                            continue

                        tool_input = block.get("input", {})
                        subagent_type = tool_input.get("subagent_type", "")

                        if "executor" in subagent_type:
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


def build_delegation_message(file_path: str) -> str:
    return """
PLAN FILE MODIFICATION BLOCKED

This is a sisyphus-speckit plan YAML file (.sisyphus/tasks/*.yaml).
NEVEREVER TRY TO MODIFY THIS FILE DIRECTLY.
ALWAYS USE SISYPHUS CLI TO WORK WITH PLANS.
```sh
sisyphus-speckit plan --help
```

```sh
sisyphus-speckit task --help
```
""".strip()


def main() -> int:
    try:
        input_raw = sys.stdin.read()
        if not input_raw.strip():
            return 0

        data: HookInput = json.loads(input_raw)
    except json.JSONDecodeError:
        return 0

    tool_name = data.get("tool_name", "")
    if tool_name not in ["Write", "Edit", "MultiEdit", "NotebookEdit"]:
        return 0

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "") or tool_input.get("notebook_path", "")

    if not file_path:
        return 0

    if not is_sisyphus_plan_yaml(file_path):
        return 0

    session_id = data.get("session_id", "")
    if not has_executor_agent(session_id):
        return 0

    message = build_delegation_message(file_path)
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
