#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Remind about active tmux sessions with claude-code- prefix (PostToolUse).

This hook checks for active tmux sessions that start with 'claude-code-'
and reminds Claude to clean them up after Bash commands complete.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, NoReturn


class Config:
    EXIT_CODE_INFORM: int = 2
    SESSION_PREFIX: str = "claude-code-"


def main() -> None:
    try:
        execute_hook_pipeline()
    except Exception:
        handle_hook_error()


def execute_hook_pipeline() -> None:
    data = parse_input()

    if not should_process(data):
        sys.exit(0)

    sessions = get_claude_code_tmux_sessions()
    handle_findings(sessions)


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
    return tool_name == "Bash"


def get_claude_code_tmux_sessions() -> list[str]:
    try:
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )

        if result.returncode != 0:
            return []

        sessions = [
            line.strip()
            for line in result.stdout.strip().split("\n")
            if line.strip().startswith(Config.SESSION_PREFIX)
        ]

        return sessions

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def handle_findings(sessions: list[str]) -> NoReturn:
    if not sessions:
        sys.exit(0)

    message = build_reminder_message(sessions)
    print(message, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_INFORM)


def build_reminder_message(sessions: list[str]) -> str:
    session_list = "\n".join(f"  - {session}" for session in sessions)

    return f"""[tmux-session-reminder]
Active Claude Code tmux sessions detected:
{session_list}

REMINDER: If you created these sessions, remember to clean them up when done:
  tmux kill-session -t <session-name>

To view session content:
  tmux capture-pane -t <session-name> -p

Check if session is still needed before killing it.
"""


def handle_hook_error() -> NoReturn:
    sys.exit(0)


if __name__ == "__main__":
    main()
