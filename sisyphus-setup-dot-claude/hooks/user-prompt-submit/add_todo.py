#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "orjson",
# ]
# ///
# pyright: reportMissingImports=false, reportUnknownArgumentType=false

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal, TypedDict

import orjson


class UserPromptSubmitInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: Literal["user-prompt-submit"]
    prompt: str


class TodoAdder:
    TODOS_DIR = Path.home() / ".claude" / "todos"

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def extract_todo_contents(self, prompt: str) -> list[str]:
        """Extract all lines starting with 'todowrite:' from the prompt."""
        todos = []
        for line in prompt.split("\n"):
            line_stripped = line.strip()
            if line_stripped.lower().startswith("todowrite:"):
                content = line_stripped[10:].strip()
                if content:
                    todos.append(content)
        return todos

    def add_todo_items(self, contents: list[str]) -> None:
        """Add multiple todo items at once in the order provided."""
        if not contents:
            return

        self.TODOS_DIR.mkdir(parents=True, exist_ok=True)
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        try:
            if todo_file.exists():
                todos: list[dict[str, str]] = orjson.loads(todo_file.read_bytes())  # type: ignore[assignment]
            else:
                todos = []
        except (orjson.JSONDecodeError, OSError):
            todos = []

        for content in reversed(contents):
            todo_item = {
                "content": content,
                "status": "pending",
                "priority": "high",
                "activeForm": content,
            }
            _ = todos.insert(0, todo_item)

        try:
            result: bytes = orjson.dumps(todos, option=orjson.OPT_INDENT_2)  # type: ignore[assignment]
            _ = todo_file.write_bytes(result)
        except OSError as e:
            print(f"Failed to write TODO file: {e}", file=sys.stderr)


def main() -> None:
    hook_filename = Path(__file__).stem.replace("_", "-")

    try:
        input_raw = sys.stdin.read()
        if not input_raw:
            sys.exit(0)

        data: UserPromptSubmitInput = orjson.loads(input_raw)  # type: ignore[assignment]
    except (orjson.JSONDecodeError, KeyError, TypeError):
        sys.exit(0)

    prompt: str = data.get("prompt", "")  # type: ignore[assignment]
    if not prompt:
        sys.exit(0)

    session_id: str = data["session_id"]  # type: ignore[assignment]
    adder = TodoAdder(session_id)

    todo_contents = adder.extract_todo_contents(prompt)
    if not todo_contents:
        sys.exit(0)

    adder.add_todo_items(todo_contents)

    todos_display = "\n".join(f'   {i + 1}. "{content}"' for i, content in enumerate(todo_contents))
    todo_count = len(todo_contents)
    warning_message = (
        f"\n[{hook_filename}]\n"
        f"📝 {todo_count} TODO(s) added from your input:\n"
        f"{todos_display}\n\n"
        f"[Added to ~/.claude/todos/{session_id}-agent-{session_id}.json]\n"
    )

    print(warning_message)
    sys.exit(0)


if __name__ == "__main__":
    main()
