#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.12"
# dependencies = [
#     "orjson",
# ]
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false
"""
User-prompt-submit hook that detects /share command and adds transcript path to todos.

When user types '/share', this hook:
1. Adds a todo item with the transcript path
2. Outputs a message to stderr so Claude can see it
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

import orjson  # pyright: ignore[reportMissingImports]


class UserPromptSubmitInput(TypedDict):
    """Input structure for UserPromptSubmit hook event."""

    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: Literal["user-prompt-submit"]
    prompt: str


class TodoItem(TypedDict):
    """Todo item structure."""

    content: str
    status: Literal["pending", "in_progress", "completed"]
    activeForm: str
    id: NotRequired[str]
    priority: NotRequired[str]


class Config:
    """Configuration constants."""

    EXIT_CODE_ALLOW: int = 0
    EXIT_CODE_BLOCK: int = 2
    TODOS_DIR = Path.home() / ".claude" / "todos"


def main() -> None:
    """Main entry point."""
    try:
        input_raw = sys.stdin.read()
        if not input_raw.strip():
            sys.exit(Config.EXIT_CODE_ALLOW)

        data: UserPromptSubmitInput = orjson.loads(input_raw)

        prompt = data.get("prompt", "").strip()
        if prompt != "/share":
            sys.exit(Config.EXIT_CODE_ALLOW)

        session_id = data.get("session_id", "")
        transcript_path = data.get("transcript_path", "")

        if not session_id or not transcript_path:
            sys.exit(Config.EXIT_CODE_ALLOW)

        add_transcript_todo(session_id, transcript_path)

        hook_filename = Path(__file__).stem.replace("_", "-")
        message = (
            f"\n[{hook_filename}]\n"
            f"📝 Transcript location added to todos:\n"
            f"   {transcript_path}\n\n"
            f"[Added to ~/.claude/todos/{session_id}-agent-{session_id}.json]\n"
        )
        print(message)

        sys.exit(Config.EXIT_CODE_ALLOW)

    except Exception:
        sys.exit(Config.EXIT_CODE_ALLOW)


def add_transcript_todo(session_id: str, transcript_path: str) -> None:
    """
    Add a todo item to get the transcript file.

    Args:
        session_id: Current session ID
        transcript_path: Path to the transcript file
    """
    Config.TODOS_DIR.mkdir(parents=True, exist_ok=True)
    todo_file = Config.TODOS_DIR / f"{session_id}-agent-{session_id}.json"

    try:
        if todo_file.exists():
            todos = orjson.loads(todo_file.read_bytes())
        else:
            todos = []
    except (orjson.JSONDecodeError, OSError):
        todos = []

    todo_id = "share-transcript"
    todo_item: TodoItem = {
        "content": f"Get transcript file at {transcript_path}",
        "status": "pending",
        "activeForm": f"Getting transcript file at {transcript_path}",
        "id": todo_id,
        "priority": "high",
    }

    for existing_todo in todos:
        if existing_todo.get("id") == todo_id:
            existing_todo["content"] = todo_item["content"]
            existing_todo["activeForm"] = todo_item["activeForm"]
            try:
                todo_file.write_bytes(orjson.dumps(todos, option=orjson.OPT_INDENT_2))
            except OSError:
                pass
            return

    todos.insert(0, todo_item)

    try:
        todo_file.write_bytes(orjson.dumps(todos, option=orjson.OPT_INDENT_2))
    except OSError:
        pass


if __name__ == "__main__":
    main()
