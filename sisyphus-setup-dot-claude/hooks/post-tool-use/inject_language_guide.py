#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "orjson",
# ]
# ///
# pyright: reportMissingImports=false, reportUnreachable=false

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, cast

import orjson


class ReadToolInput(TypedDict):
    file_path: str


class WriteToolInput(TypedDict):
    file_path: str
    content: str


class EditToolInput(TypedDict):
    file_path: str
    old_string: str
    new_string: str
    replace_all: NotRequired[bool]


ToolInput = ReadToolInput | WriteToolInput | EditToolInput


class PostToolUseInput(TypedDict):
    session_id: str
    tool_name: Literal["Read", "Write", "Edit"]
    transcript_path: str
    cwd: str
    hook_event_name: Literal["post-tool-use"]
    tool_input: ToolInput
    tool_response: dict[str, Any]


class ToolUseBlock(TypedDict):
    type: Literal["tool_use"]
    name: Literal["Read"] | str
    id: str
    input: dict[str, Any]


class ToolResultBlock(TypedDict):
    type: Literal["tool_result"]
    tool_use_id: str
    content: str | list[dict[str, Any]]
    is_error: NotRequired[bool]


class TextBlock(TypedDict):
    type: Literal["text"]
    text: str


ContentBlock = ToolUseBlock | ToolResultBlock | TextBlock


class AssistantMessage(TypedDict):
    role: Literal["assistant"]
    content: list[ContentBlock]


class UserMessage(TypedDict):
    role: Literal["user"]
    content: str | list[ContentBlock]


class TranscriptEntry(TypedDict):
    type: Literal["user", "assistant"]
    message: AssistantMessage | UserMessage
    timestamp: NotRequired[str]


class RawTranscriptEntry(TypedDict):
    type: str
    message: dict[str, Any]
    timestamp: NotRequired[str]


class LanguageGuideChecker:
    """Checks language-specific guide compliance when reading code files."""

    MODULAR_PROMPTS_DIR = Path.home() / ".claude" / "modular-prompts" / "languages"
    TODOS_DIR = Path.home() / ".claude" / "todos"

    def __init__(self, cwd: str, transcript_path: str, session_id: str) -> None:
        self.cwd = Path(cwd)
        self.transcript_path = Path(transcript_path)
        self.session_id = session_id

    def _generate_todo_id(self, file_extension: str) -> str:
        """Generate todo ID for a language guide."""
        return f"read-guide-{file_extension.lower()}"

    def _mark_todo_completed(self, todo_id: str) -> None:
        """Mark an existing todo item as completed."""
        self.TODOS_DIR.mkdir(parents=True, exist_ok=True)
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        if not todo_file.exists():
            return

        try:
            todos = cast(list[dict[str, Any]], orjson.loads(todo_file.read_bytes()))
        except (orjson.JSONDecodeError, OSError):
            return

        for todo in todos:
            if todo.get("id") == todo_id:
                if todo.get("status") != "completed":
                    todo["status"] = "completed"
                break

        try:
            _ = todo_file.write_bytes(cast(bytes, orjson.dumps(todos, option=orjson.OPT_INDENT_2)))
        except OSError:
            pass

    def _check_and_complete_existing_todos(self) -> None:
        """Check existing todos and mark as completed if guide has been read in transcript."""
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        if not todo_file.exists():
            return

        try:
            todos = cast(list[dict[str, Any]], orjson.loads(todo_file.read_bytes()))
        except (orjson.JSONDecodeError, OSError):
            return

        if not isinstance(todos, list):
            return

        modified = False
        for todo in todos:
            todo_id = todo.get("id", "")
            if not todo_id.startswith("read-guide-"):
                continue

            if todo.get("status") == "completed":
                continue

            lang_ext = todo_id.replace("read-guide-", "").lower()
            guide_path = self.MODULAR_PROMPTS_DIR / f"{lang_ext}.md"

            if guide_path.exists() and self._has_guide_been_read(guide_path):
                todo["status"] = "completed"
                modified = True

        if modified:
            try:
                _ = todo_file.write_bytes(cast(bytes, orjson.dumps(todos, option=orjson.OPT_INDENT_2)))
            except OSError:
                pass

    def _get_guide_path(self, extension: str) -> Path | None:
        if not extension or not extension.startswith("."):
            return None

        guide_filename = f"{extension[1:]}.md"
        guide_path = self.MODULAR_PROMPTS_DIR / guide_filename

        return guide_path if guide_path.exists() else None

    def _get_guide_content(self, guide_path: Path) -> str | None:
        if not guide_path.exists():
            return None

        try:
            return guide_path.read_text(encoding="utf-8")
        except OSError:
            return None

    def _get_guide_identifier(self, _guide_content: str, guide_filename: str) -> str:
        return f"[language-guide:{guide_filename}]"

    def _has_guide_been_read(self, guide_path: Path) -> bool:
        if not self.transcript_path.exists():
            return False

        try:
            guide_path_str = str(guide_path.resolve())
            transcript_content = self.transcript_path.read_text(encoding="utf-8")

            for line in transcript_content.splitlines():
                if not line.strip():
                    continue

                try:
                    entry: RawTranscriptEntry = cast(RawTranscriptEntry, orjson.loads(line))
                except orjson.JSONDecodeError:
                    continue

                if not isinstance(entry, dict):
                    continue

                if entry.get("type") != "assistant":
                    continue

                message = entry.get("message")
                if not isinstance(message, dict):
                    continue

                if message.get("role") != "assistant":
                    continue

                content = message.get("content")
                if not isinstance(content, list):
                    continue

                for block in content:
                    if not isinstance(block, dict):
                        continue

                    if block.get("type") != "tool_use":
                        continue

                    if block.get("name") != "Read":
                        continue

                    tool_input = block.get("input")
                    if not isinstance(tool_input, dict):
                        continue

                    if tool_input.get("file_path") == guide_path_str:
                        return True

            return False

        except OSError:
            return False

    def _add_todo_item(self, guide_path: Path, file_extension: str) -> None:
        self.TODOS_DIR.mkdir(parents=True, exist_ok=True)
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        try:
            if todo_file.exists():
                todos = cast(list[dict[str, Any]], orjson.loads(todo_file.read_bytes()))
            else:
                todos = []
        except (orjson.JSONDecodeError, OSError):
            todos = []

        todo_id = self._generate_todo_id(file_extension)

        todo_item = {
            "content": f"Read {file_extension} language guide: {guide_path}",
            "status": "pending",
            "priority": "high",
            "id": todo_id,
        }

        for existing_todo in todos:
            if existing_todo.get("id") == todo_item["id"]:
                return

        _ = todos.insert(0, todo_item)

        try:
            _ = todo_file.write_bytes(cast(bytes, orjson.dumps(todos, option=orjson.OPT_INDENT_2)))
        except OSError:
            pass

    def check_and_inject(self, file_path: str) -> str:
        path = Path(file_path)

        if path.parent == self.MODULAR_PROMPTS_DIR and path.suffix == ".md":
            file_extension = path.stem.upper()
            todo_id = self._generate_todo_id(file_extension)
            self._mark_todo_completed(todo_id)
            return ""

        extension = path.suffix
        guide_path = self._get_guide_path(extension)
        if not guide_path:
            return ""

        guide_content = self._get_guide_content(guide_path)
        if not guide_content:
            return ""

        file_extension = extension[1:].upper()

        if self._has_guide_been_read(guide_path):
            todo_id = self._generate_todo_id(file_extension)
            self._mark_todo_completed(todo_id)
            return ""

        self._add_todo_item(guide_path, file_extension)

        warning_message = (
            f"ACTION REQUIRED: Use Read tool to read guide for {file_extension} immediately. READ NOW."
            f"You MUST read the following guide before proceeding with {path.name}:\n"
            f"{guide_path}\n\n"
            f"[Todo added to ~/.claude/todos/{self.session_id}-agent-{self.session_id}.json]\n"
        )

        return warning_message


def main() -> None:
    """Main entry point for the hook."""
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    try:
        input_raw = sys.stdin.read()
        if not input_raw:
            print(f"[{hook_filename}] Skipping: No input provided")
            sys.exit(0)

        data: PostToolUseInput = cast(PostToolUseInput, orjson.loads(input_raw))
    except (orjson.JSONDecodeError, KeyError, TypeError):
        print(f"[{hook_filename}] Skipping: Invalid input format")
        sys.exit(0)

    tool_input = data["tool_input"]
    file_path = tool_input.get("file_path", "")

    if not file_path:
        print(f"[{hook_filename}] Skipping: No file path provided")
        sys.exit(0)

    if Path(file_path).resolve() == Path(__file__).resolve():
        print(f"[{hook_filename}] Skipping: Self-reference detected")
        sys.exit(0)

    cwd = data["cwd"]
    transcript_path = data["transcript_path"]
    session_id = data["session_id"]

    checker = LanguageGuideChecker(cwd, transcript_path, session_id)
    message = checker.check_and_inject(file_path)

    if message:
        print(message, file=sys.stderr)
        sys.exit(2)

    print(f"[{hook_filename}] Success: No compliance check needed")
    sys.exit(0)


if __name__ == "__main__":
    main()
