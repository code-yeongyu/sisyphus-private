#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Block executor agent calls without /execute command (PreToolUse hook).

Prevents direct executor agent invocations when no /execute command exists in transcript.
Ensures proper orchestration workflow is followed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NotRequired, TypedDict


class ToolInput(TypedDict):
    """Tool input structure."""

    subagent_type: NotRequired[str]


class PreToolUseInput(TypedDict):
    """PreToolUse hook input structure."""

    session_id: str
    tool_name: str
    tool_input: ToolInput
    cwd: str


class Config:
    """Configuration constants."""

    EXIT_CODE_ALLOW: int = 0
    EXIT_CODE_BLOCK: int = 2
    EXECUTOR_SUBAGENT: str = "executor"
    TASK_TOOL: str = "Task"


def main() -> None:
    """Main entry point."""
    try:
        execute_hook()
    except Exception:
        # Gracefully allow on unexpected errors
        sys.exit(Config.EXIT_CODE_ALLOW)


def execute_hook() -> None:
    """Execute the hook logic."""
    data = parse_input()

    if not should_check_executor(data):
        sys.exit(Config.EXIT_CODE_ALLOW)

    session_id = data.get("session_id", "")
    if has_execute_command(session_id):
        sys.exit(Config.EXIT_CODE_ALLOW)

    # Block executor call
    print_blocking_message()
    sys.exit(Config.EXIT_CODE_BLOCK)


def parse_input() -> dict[str, Any]:
    """Parse stdin JSON input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(Config.EXIT_CODE_ALLOW)

    try:
        return json.loads(input_raw)
    except json.JSONDecodeError:
        sys.exit(Config.EXIT_CODE_ALLOW)


def should_check_executor(data: dict[str, Any]) -> bool:
    """Check if this is an executor agent call."""
    tool_name = data.get("tool_name", "")
    if tool_name != Config.TASK_TOOL:
        return False

    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return False

    subagent_type = tool_input.get("subagent_type", "")
    return subagent_type == Config.EXECUTOR_SUBAGENT


def has_execute_command(session_id: str) -> bool:
    """
    Check if /execute command exists in transcript.
    Checks both current transcript and pre-compact backups.
    """
    if not session_id:
        return False

    # Check current transcript
    transcript_path = find_current_transcript(session_id)
    if transcript_path and check_execute_in_transcript(transcript_path):
        return True

    # Check pre-compact backups
    backups = find_pre_compact_backups(session_id)
    for backup_path in backups:
        if check_execute_in_transcript(backup_path):
            return True

    return False


def find_current_transcript(session_id: str) -> Path | None:
    """Find current transcript file for session."""
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


def check_execute_in_transcript(transcript_path: Path) -> bool:
    """Check if transcript contains /execute command."""
    try:
        with transcript_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)

                    if data.get("type") != "user":
                        continue

                    message = data.get("message", {})
                    content = message.get("content", "")

                    match content:
                        case str():
                            if "<command-name>/execute</command-name>" in content:
                                return True
                        case list():
                            for item in content:
                                if isinstance(item, dict):
                                    text = item.get("text", "")
                                    if "<command-name>/execute</command-name>" in text:
                                        return True

                except json.JSONDecodeError:
                    continue

        return False

    except Exception:
        return False


def print_blocking_message() -> None:
    """Print blocking error message to stderr."""
    message = """
========================================
⛔ EXECUTOR CALL BLOCKED
========================================

[ERROR] Cannot invoke executor agent without explicit user request

You attempted to call @agent-executor, but there is no /execute command in the session transcript.

REASON:
- executor agents should only be invoked through the /execute orchestrator command
- Direct executor calls bypass proper orchestration and tracking
- User must explicitly run /execute to start systematic task execution

ACTION REQUIRED:
1. If you intended to start task execution:
   → Ask user to run: /execute <todo-list-path>

2. If you mistakenly marked tasks as "in_progress":
   → Use TodoWrite to revert tasks back to "pending" status
   → Wait for user's explicit /execute command

3. If this is blocking legitimate work:
   → Check that you're following the correct workflow
   → Verify session transcript has /execute command

DO NOT attempt to bypass this check. Proper orchestration ensures:
- Systematic task tracking
- Knowledge accumulation in notepad.md
- Proper verification and validation
- Clear progress reporting to user

Use /execute command for proper task orchestration.
"""
    print(message, file=sys.stderr)


if __name__ == "__main__":
    main()
