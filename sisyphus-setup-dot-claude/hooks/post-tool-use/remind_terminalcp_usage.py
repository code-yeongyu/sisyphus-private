#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Remind users about terminalcp when using Bash for interactive tasks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NoReturn


class Config:
    EXIT_CODE_INFORM: int = 2


TERMINALCP_REMINDER_MESSAGE = """<system-reminder>
Consider using terminalcp for interactive CLI/TUI tasks:
- Debuggers (pdb/gdb/lldb/node inspect), REPLs (Python/Node/Ruby)
- Database CLIs (psql/mysql/redis-cli), Framework shells (Django/Rails)
Load: Skill tool with command "interactive-terminal"
</system-reminder>"""


def main() -> None:
    try:
        execute_hook_pipeline()
    except Exception:
        handle_hook_error()


def execute_hook_pipeline() -> None:
    data = parse_input()

    if not should_process(data):
        sys.exit(0)

    handle_findings()


def parse_input() -> dict[str, Any]:
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        return json.loads(input_raw)
    except json.JSONDecodeError:
        sys.exit(0)


def should_process(data: dict[str, Any]) -> bool:
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return False

    session_id = data.get("session_id", "")
    if has_interactive_terminal_skill(session_id):
        return False

    return True


def find_session_transcript(session_id: str) -> Path | None:
    """Find current session transcript file."""
    if not session_id:
        return None

    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return None

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        session_file = project_dir / f"{session_id}.jsonl"
        if session_file.exists():
            return session_file

    return None


def find_pre_compact_backups(session_id: str) -> list[Path]:
    """Find pre-compact backup files for session (oldest to newest)."""
    backup_dir = Path.home() / ".claude" / "pre-compact-session-histories"
    if not backup_dir.exists():
        return []

    backups = list(backup_dir.glob(f"{session_id}-*.jsonl"))
    backups.sort(key=lambda p: p.name)
    return backups


def check_skill_in_transcript(transcript_path: Path) -> bool:
    """Check if transcript contains interactive-terminal skill usage."""
    try:
        with transcript_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)

                    if data.get("type") not in ("user", "assistant"):
                        continue

                    message = data.get("message", {})
                    content = message.get("content", [])

                    match content:
                        case str():
                            if "<command-name>interactive-terminal</command-name>" in content:
                                return True
                        case list():
                            for item in content:
                                if isinstance(item, dict):
                                    text = item.get("text", "")
                                    if "<command-name>interactive-terminal</command-name>" in text:
                                        return True
                        case _:
                            pass

                except json.JSONDecodeError:
                    continue

        return False

    except Exception:
        return False


def has_interactive_terminal_skill(session_id: str) -> bool:
    """
    Check if interactive-terminal skill was loaded in this session.
    Checks both current transcript and pre-compact backups.
    """
    if not session_id:
        return False

    transcript_path = find_session_transcript(session_id)
    if transcript_path and check_skill_in_transcript(transcript_path):
        return True

    backups = find_pre_compact_backups(session_id)
    for backup_path in backups:
        if check_skill_in_transcript(backup_path):
            return True

    return False


def handle_findings() -> NoReturn:
    print(TERMINALCP_REMINDER_MESSAGE, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_INFORM)


def handle_hook_error() -> NoReturn:
    sys.exit(0)


if __name__ == "__main__":
    main()
