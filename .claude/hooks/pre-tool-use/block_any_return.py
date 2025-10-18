#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ast-grep-py>=0.24.1",
# ]
# ///
"""
Any return type detector hook for Claude Code.
Blocks edits that contain functions with Any return type and suggests explicit types.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import (
    Any,
    Literal,
    NoReturn,
    NotRequired,
    TypedDict,
)

import ast_grep_py as sg


class Config:
    """Configuration constants for the hook."""

    EXIT_CODE_BLOCK_TOOL: int = 2
    DEFAULT_TEXT_TRUNCATION: int = 80
    TAB: str = "\t"


class AnyReturnIssue(TypedDict):
    type: Literal["function", "method", "async_function", "async_method"]
    issue_description: str
    suggestion: str
    line: int
    column: int
    end_line: int
    end_column: int
    function_name: str
    text: str


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


def run_any_return_check() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        _execute_hook_pipeline()
    except Exception as e:
        _handle_hook_error(e)


def detect_any_return_violations(code: str) -> list[AnyReturnIssue]:
    """Detect all functions with Any return type in the given code."""
    root: sg.SgRoot = sg.SgRoot(code, "python")
    node: sg.SgNode = root.root()

    violations: list[AnyReturnIssue] = []

    function_nodes: list[sg.SgNode] = node.find_all(pattern="def $FUNC($$$ARGS) -> $RETURN: $$$BODY")

    for func_node in function_nodes:
        return_match = func_node.get_match("RETURN")
        if not return_match:
            continue

        return_text = return_match.text()

        if "Any" not in return_text:
            continue

        if _should_allow_any_usage(return_text):
            continue

        func_match = func_node.get_match("FUNC")
        if not func_match:
            continue
        func_name = func_match.text()

        func_text = func_node.text()
        is_async = func_text.strip().startswith("async ")
        is_method = _is_method(func_node)

        if is_async:
            func_type = "async_method" if is_method else "async_function"
        else:
            func_type = "method" if is_method else "function"

        issue = _create_any_return_issue(func_node=func_node, func_name=func_name, func_type=func_type)
        violations.append(issue)

    return violations


def _should_allow_any_usage(return_type: str) -> bool:
    """Determine if an Any usage in return type should be allowed.

    We want to block most uses of Any in return types, but allow:
    - TypeVar bounds that happen to be named with "Any" in them
    - Callable types where Any is only in input parameters

    Returns True if the usage should be ALLOWED (not blocked).
    """
    cleaned = return_type.replace(" ", "")

    # Complex pattern: Callable[[Any], str] allowed, Callable[[str], Any] blocked
    if "Callable[[" in cleaned:
        if "]," in cleaned or "]->" in cleaned:
            parts = cleaned.split("],") if "]," in cleaned else cleaned.split("]->")
            if len(parts) > 1:
                return_part = parts[1].rstrip("]")
                if "Any" not in return_part:
                    return True

    return False


def _is_method(func_node: sg.SgNode) -> bool:
    """Check if a function node is a method (inside a class)."""
    current: sg.SgNode | None = func_node.parent()
    while current:
        if current.kind() == "class_definition":
            return True
        current = current.parent()
    return False


def _create_any_return_issue(
    func_node: sg.SgNode,
    func_name: str,
    func_type: Literal["function", "method", "async_function", "async_method"],
) -> AnyReturnIssue:
    """Create an AnyReturnIssue from a function node."""
    start = func_node.range().start
    end = func_node.range().end

    type_labels = {
        "function": "Function",
        "method": "Method",
        "async_function": "Async function",
        "async_method": "Async method",
    }

    type_label = type_labels[func_type]

    issue_description = f"{type_label} '{func_name}' has return type 'Any'"

    func_text = func_node.text()
    if " -> " in func_text:
        first_line = func_text.split("\n")[0]
        if " -> " in first_line:
            return_part = first_line.split(" -> ")[1].split(":")[0].strip()
            suggestion = (
                f"Replace '{return_part}' with a specific type like 'str', 'int', 'list[str]', 'CustomClass', etc."
            )
        else:
            suggestion = "Replace 'Any' with a specific type"
    else:
        suggestion = "Add explicit return type annotation"

    return AnyReturnIssue(
        type=func_type,
        issue_description=issue_description,
        suggestion=suggestion,
        line=start.line + 1,
        column=start.column,
        end_line=end.line + 1,
        end_column=end.column,
        function_name=func_name,
        text=_truncate_text(func_text, Config.DEFAULT_TEXT_TRUNCATION),
    )


def build_error_message(violations: list[AnyReturnIssue], file_path: str) -> str:
    """Build error message for Any return type violations."""
    if not violations:
        return ""

    display_path: str = _get_display_path(file_path)

    msg_parts: list[str] = []
    msg_parts.append("CRITICAL ERROR: ANY RETURN TYPE DETECTED - OPERATION BLOCKED\n")
    msg_parts.append("=" * 60 + "\n\n")
    msg_parts.append(f"File: {display_path}\n")
    msg_parts.append(f"Violations found: {len(violations)}\n\n")
    msg_parts.append("Functions with 'Any' return type must specify explicit types.\n")
    msg_parts.append("Type safety is crucial for maintainable code.\n\n")

    for i, violation in enumerate(violations, 1):
        msg_parts.append(f"[{i}] Line {violation['line']}: {violation['issue_description']}\n")
        msg_parts.append(f"\tCode: {violation['text']}\n")
        msg_parts.append(f"\tFix: {violation['suggestion']}\n\n")

    msg_parts.append("-" * 60 + "\n")
    msg_parts.append("Common return type examples:\n")
    msg_parts.append("\t- str, int, float, bool\n")
    msg_parts.append("\t- list[str], dict[str, int], tuple[int, str]\n")
    msg_parts.append("\t- Optional[str], Union[str, int]\n")
    msg_parts.append("\t- YourCustomClass, pd.DataFrame, np.ndarray\n")
    msg_parts.append("\t- None (for functions that don't return anything)\n\n")
    msg_parts.append("This operation has been BLOCKED. Fix the return types above to proceed.\n")

    return "".join(msg_parts)


def adjust_line_numbers_for_edit(
    violations: list[AnyReturnIssue],
    file_path: str,
    tool_input: dict[str, Any],
) -> list[AnyReturnIssue]:
    """Adjust line numbers for Edit tool based on position in file."""
    if not violations or not file_path or not Path(file_path).exists():
        return violations

    try:
        with open(file_path, encoding="utf-8") as f:
            full_content: str = f.read()

        old_string: str = tool_input.get("old_string", "")
        new_string: str = tool_input.get("new_string", "")

        index: int = full_content.find(old_string) if old_string else full_content.find(new_string)

        if index != -1:
            lines_before: int = full_content[:index].count("\n")
            for violation in violations:
                violation["line"] += lines_before
    except Exception:
        pass

    return violations


def parse_input() -> InputData:
    """Parse and validate stdin input."""
    input_raw: str = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        parsed_data: InputData = json.loads(input_raw)
        return parsed_data
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing input: {e}", file=sys.stderr)
        sys.exit(0)


def should_process(data: InputData) -> bool:
    """Determine if the input should be processed."""
    tool_name: str = data.get("tool_name", "")
    tool_input: WriteToolInput | EditToolInput | MultiEditToolInput | None = data.get("tool_input")

    if not tool_name or not tool_input:
        return False

    if not isinstance(tool_input, dict):
        return False

    file_path: str = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith(".py"):
        return False

    excluded: bool = _is_excluded_path(file_path)
    return not excluded


def process_tool_input(data: InputData) -> list[AnyReturnIssue]:
    """Process tool input and detect violations."""
    tool_name: str = data.get("tool_name", "")
    tool_input: Any = data.get("tool_input", {})

    if not isinstance(tool_input, dict):
        return []

    processors: dict[str, Any] = {
        "Write": _process_write_tool,
        "Edit": _process_edit_tool,
        "MultiEdit": _process_multiedit_tool,
    }

    processor = processors.get(tool_name)
    result: list[AnyReturnIssue] = processor(tool_input) if processor else []
    return result


def handle_findings(violations: list[AnyReturnIssue], file_path: str) -> NoReturn:
    """Handle detected violations and exit appropriately."""
    if not violations:
        sys.exit(0)

    message: str = build_error_message(violations, file_path)

    if message.strip():
        print(message, file=sys.stderr)
        sys.exit(Config.EXIT_CODE_BLOCK_TOOL)

    sys.exit(0)


def extract_file_path(data: InputData) -> str:
    """Extract file path from input data."""
    tool_input: Any = data.get("tool_input", {})
    if isinstance(tool_input, dict):
        file_path: str = tool_input.get("file_path", "")
        return file_path
    return ""


def _execute_hook_pipeline() -> NoReturn:
    """Execute the main hook logic pipeline."""
    data: InputData = parse_input()
    if not should_process(data):
        sys.exit(0)
    violations: list[AnyReturnIssue] = process_tool_input(data)
    file_path: str = extract_file_path(data)
    handle_findings(violations, file_path)


def _handle_hook_error(e: Exception) -> NoReturn:
    """Handle errors in hook execution."""
    print(f"ERROR in hook: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(0)


def _is_excluded_path(file_path: str) -> bool:
    """Check if file path should be excluded from processing."""
    if (
        "/test/" in file_path
        or "/tests/" in file_path
        or file_path.endswith("_test.py")
        or "test_" in Path(file_path).name
    ):
        return True

    if "/hooks/" in file_path:
        return True

    if "/migrations/" in file_path:
        return True

    return False


def _process_write_tool(tool_input: dict[str, Any]) -> list[AnyReturnIssue]:
    """Process Write tool input."""
    content: str = tool_input.get("content", "")
    result: list[AnyReturnIssue] = detect_any_return_violations(content) if content else []
    return result


def _process_edit_tool(tool_input: dict[str, Any]) -> list[AnyReturnIssue]:
    """Process Edit tool input."""
    new_string: str = tool_input.get("new_string", "")
    if not new_string:
        return []

    violations: list[AnyReturnIssue] = detect_any_return_violations(new_string)
    file_path: str = tool_input.get("file_path", "")
    adjusted_violations: list[AnyReturnIssue] = adjust_line_numbers_for_edit(violations, file_path, tool_input)
    return adjusted_violations


def _process_multiedit_tool(tool_input: dict[str, Any]) -> list[AnyReturnIssue]:
    """Process MultiEdit tool input."""
    violations: list[AnyReturnIssue] = []
    edits: list[Any] = tool_input.get("edits", [])

    for edit in edits:
        if isinstance(edit, dict):
            new_string: str = edit.get("new_string", "")
            if new_string:
                detected_violations: list[AnyReturnIssue] = detect_any_return_violations(new_string)
                violations.extend(detected_violations)

    return violations


def _get_display_path(file_path: str) -> str:
    """Get display-friendly path relative to cwd if possible."""
    cwd: Path = Path.cwd()
    try:
        path_obj: Path = Path(file_path).resolve()
        if path_obj.is_relative_to(cwd):
            relative_path: Path = path_obj.relative_to(cwd)
            result: str = str(relative_path)
            return result
        return file_path
    except (ValueError, OSError):
        return file_path


def _truncate_text(text: str, max_length: int = Config.DEFAULT_TEXT_TRUNCATION) -> str:
    """Truncate text to specified length with ellipsis if needed."""
    if len(text) <= max_length:
        return text

    lines: list[str] = text.split("\n")
    if len(lines) > 1:
        first_line: str = lines[0]
        if len(first_line) > max_length - 3:
            truncated: str = first_line[: max_length - 3] + "..."
            return truncated
        return first_line + "..."

    truncated_text: str = text[: max_length - 3] + "..."
    return truncated_text


if __name__ == "__main__":
    run_any_return_check()
