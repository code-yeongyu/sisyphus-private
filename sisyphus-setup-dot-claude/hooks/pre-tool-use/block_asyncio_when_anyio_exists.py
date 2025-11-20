#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "toml>=0.10.2",
#   "ast-grep-py>=0.24.1",
# ]
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false, reportUnknownArgumentType=false
"""
Asyncio blocker hook for Claude Code when anyio is available.
Blocks edits that use asyncio when anyio is available in the project.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any, NoReturn, NotRequired, TypedDict

import ast_grep_py as sg  # type: ignore[import-not-found]
import toml


class Config:
    """Configuration constants for the hook."""

    EXIT_CODE_BLOCK_TOOL: int = 2
    TAB: str = "\t"


class Violation(TypedDict):
    line: int
    text: str
    issue_type: str


class WriteToolInput(TypedDict):
    file_path: str
    content: str


class EditToolInput(TypedDict):
    file_path: str
    new_string: str
    old_string: NotRequired[str]


class EditEntry(TypedDict):
    new_string: str
    old_string: NotRequired[str]


class MultiEditToolInput(TypedDict):
    file_path: str
    edits: list[EditEntry]


class InputData(TypedDict):
    session_id: NotRequired[str]
    transcript_path: NotRequired[str]
    cwd: NotRequired[str]
    hook_event_name: NotRequired[str]
    tool_name: NotRequired[str]
    tool_input: NotRequired[WriteToolInput | EditToolInput | MultiEditToolInput]


def main() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        _execute_hook_pipeline()
    except Exception as e:
        _handle_hook_error(e)


def _build_error_message(violations: list[Violation], file_path: str) -> str:
    """Build error message for asyncio usage violations."""
    if not violations:
        return ""

    display_path = _get_display_path(file_path)

    msg_parts: list[str] = []
    msg_parts.append("CRITICAL ERROR: ASYNCIO DETECTED WHEN ANYIO IS AVAILABLE\n")
    msg_parts.append("=" * 60 + "\n\n")
    msg_parts.append(f"File: {display_path}\n")
    msg_parts.append(f"Violations found: {len(violations)}\n\n")
    msg_parts.append("This project uses 'anyio' for async operations.\n")
    msg_parts.append("Using 'asyncio' directly would bypass anyio's structured concurrency benefits.\n\n")

    for violation in violations[:10]:
        issue_descriptions: dict[str, str] = {
            "import_asyncio": "Direct asyncio import",
            "import_asyncio_as": "Import asyncio with alias",
            "from_asyncio_import": "From asyncio import",
            "from_asyncio_submodule": "From asyncio submodule import",
            "asyncio_attribute": "Asyncio attribute access",
            "asyncio_call": "Asyncio function call",
        }
        issue_desc = issue_descriptions.get(violation["issue_type"], "Asyncio usage")

        msg_parts.append(f"Line {violation['line']}: {issue_desc}\n")
        msg_parts.append(f"\tCode: {violation['text']}\n\n")

    if len(violations) > 10:
        msg_parts.append(f"... and {len(violations) - 10} more violations\n\n")

    msg_parts.append("-" * 60 + "\n")
    msg_parts.append("Replace asyncio with anyio equivalents:\n")
    msg_parts.append("\t- asyncio.run() → anyio.run()\n")
    msg_parts.append("\t- asyncio.create_task() → task_group.start_soon()\n")
    msg_parts.append("\t- asyncio.sleep() → anyio.sleep()\n")
    msg_parts.append("\t- asyncio.gather() → anyio.create_task_group()\n")
    msg_parts.append("\t- asyncio.Queue() → anyio.create_memory_object_stream()\n\n")
    msg_parts.append("This operation has been BLOCKED. Use anyio instead of asyncio.\n")

    return "".join(msg_parts)


def check_anyio_exists() -> bool:
    """Check if anyio is explicitly declared in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return False

    try:
        with open(pyproject_path) as f:
            config = toml.load(f)

        if "dependencies" in config.get("project", {}):
            dependencies = config["project"]["dependencies"]
            if any("anyio" in dep.lower() for dep in dependencies):
                return True

        if "tool" in config and "poetry" in config["tool"]:
            poetry_deps = config["tool"]["poetry"].get("dependencies", {})
            if "anyio" in poetry_deps:
                return True

            dev_deps = config["tool"]["poetry"].get("group", {}).get("dev", {}).get("dependencies", {})
            if "anyio" in dev_deps:
                return True

    except (toml.TomlDecodeError, KeyError, TypeError):
        pass

    return False


def detect_asyncio_usage(code: str) -> list[Violation]:
    """Detect asyncio usage in the given code using ast-grep."""
    violations: list[Violation] = []

    root = sg.SgRoot(code, "python")  # type: ignore[arg-type]
    node = root.root()  # type: ignore[attr-defined]

    patterns: list[tuple[str, str]] = [
        ("import_asyncio", "import asyncio"),
        ("import_asyncio_as", "import asyncio as $_"),
        ("from_asyncio_import", "from asyncio import $_"),
        ("from_asyncio_submodule", "from asyncio.$_ import $_"),
        ("asyncio_attribute", "asyncio.$_"),
        ("asyncio_call", "asyncio.$_($_)"),
    ]

    for issue_type, pattern in patterns:
        matches = node.find_all(pattern=pattern)  # type: ignore[attr-defined]
        for match in matches:  # type: ignore[attr-defined]
            match_range = match.range()  # type: ignore[attr-defined]
            line = match_range.start.line + 1  # type: ignore[attr-defined]
            text: str = match.text()  # type: ignore[attr-defined]

            if len(text) > 100:
                text = text[:100]

            violations.append(
                Violation(
                    line=line,
                    text=text,
                    issue_type=issue_type,
                )
            )

    violations.sort(key=lambda v: v["line"])

    seen: set[tuple[int, str]] = set()
    unique_violations: list[Violation] = []
    for v in violations:
        key = (v["line"], v["text"])
        if key not in seen:
            seen.add(key)
            unique_violations.append(v)

    return unique_violations


def extract_file_path(data: InputData) -> str:
    """Extract file path from input data."""
    tool_input: Any = data.get("tool_input", {})
    if isinstance(tool_input, dict):
        file_path = tool_input.get("file_path", "")
        return file_path
    return ""


def handle_findings(violations: list[Violation], file_path: str, anyio_exists: bool) -> NoReturn:
    """Handle detected violations and exit appropriately."""
    if not violations or not anyio_exists:
        sys.exit(0)

    message = _build_error_message(violations, file_path)

    if message.strip():
        print(message, file=sys.stderr)
        sys.exit(Config.EXIT_CODE_BLOCK_TOOL)

    sys.exit(0)


def parse_input() -> InputData:
    """Parse and validate stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        parsed_data: InputData = json.loads(input_raw)
        return parsed_data
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing input: {e}", file=sys.stderr)
        sys.exit(0)


def process_tool_input(data: InputData) -> list[Violation]:
    """Process tool input and detect violations."""
    tool_name = data.get("tool_name", "")
    tool_input: Any = data.get("tool_input", {})

    if not isinstance(tool_input, dict):
        return []

    processors: dict[str, Any] = {
        "Write": _process_write_tool,
        "Edit": _process_edit_tool,
        "MultiEdit": _process_multiedit_tool,
    }

    processor = processors.get(tool_name)
    result: list[Violation] = processor(tool_input) if processor else []
    return result


def should_process(data: InputData) -> bool:
    """Determine if the input should be processed."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input")

    if not tool_name or not tool_input:
        return False

    if not isinstance(tool_input, dict):
        return False

    file_path = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith(".py"):
        return False

    return True


def _execute_hook_pipeline() -> NoReturn:
    """Execute the main hook logic pipeline."""
    data = parse_input()
    if not should_process(data):
        sys.exit(0)

    anyio_exists = check_anyio_exists()
    if not anyio_exists:
        sys.exit(0)

    violations = process_tool_input(data)
    file_path = extract_file_path(data)
    handle_findings(violations, file_path, anyio_exists)


def _get_display_path(file_path: str) -> str:
    """Get display-friendly path relative to cwd if possible."""
    cwd = Path.cwd()
    try:
        path_obj = Path(file_path).resolve()
        if path_obj.is_relative_to(cwd):
            relative_path = path_obj.relative_to(cwd)
            result = str(relative_path)
            return result
        return file_path
    except (ValueError, OSError):
        return file_path


def _handle_hook_error(e: Exception) -> NoReturn:
    """Handle errors in hook execution."""
    print(f"ERROR in hook: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(0)


def _process_edit_tool(tool_input: dict[str, Any]) -> list[Violation]:
    """Process Edit tool input."""
    new_string = tool_input.get("new_string", "")
    if not new_string:
        return []

    violations = detect_asyncio_usage(new_string)
    return violations


def _process_multiedit_tool(tool_input: dict[str, Any]) -> list[Violation]:
    """Process MultiEdit tool input."""
    violations: list[Violation] = []
    edits = tool_input.get("edits", [])

    for edit in edits:
        if isinstance(edit, dict):
            new_string = edit.get("new_string", "")
            if new_string:
                detected_violations = detect_asyncio_usage(new_string)
                violations.extend(detected_violations)

    return violations


def _process_write_tool(tool_input: dict[str, Any]) -> list[Violation]:
    """Process Write tool input."""
    content = tool_input.get("content", "")
    result = detect_asyncio_usage(content) if content else []
    return result


if __name__ == "__main__":
    main()
