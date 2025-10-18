#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ast-grep-py>=0.24.1",
# ]
# ///
"""
Nested import detector hook for Claude Code.
Blocks edits that contain imports inside functions/methods and suggests alternatives.
"""

from __future__ import annotations

import json
import re
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from re import Pattern
from typing import (
    Any,
    Literal,
    NoReturn,
    NotRequired,
    TextIO,
    TypedDict,
)

import ast_grep_py as sg

TYPE_IGNORE_PATTERN: Pattern[str] = re.compile(r"#\s*type:\s*ignore(?:\[[\w,\s]+\])?(?:\s|$)")


class Config:
    """Configuration constants for the hook."""

    EXIT_CODE_BLOCK_TOOL: int = 2
    DEFAULT_TEXT_TRUNCATION: int = 80
    LONG_TEXT_TRUNCATION: int = 120
    TAB: str = "\t"


class NestedImportIssue(TypedDict):
    type: Literal["import", "from_import"]
    issue_description: str
    suggestion: str
    line: int
    column: int
    end_line: int
    end_column: int
    function_name: str
    module_name: str
    text: str
    is_type_checking: bool
    from_items: str | None


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


class ImportContext:
    """Context for creating nested import issues."""

    def __init__(
        self,
        import_type: Literal["import", "from_import"],
        import_node: sg.SgNode,
        function_name: str,
        module_name: str,
        is_type_checking: bool,
        from_items: str | None,
    ) -> None:
        self.import_type: Literal["import", "from_import"] = import_type
        self.import_node: sg.SgNode = import_node
        self.function_name: str = function_name
        self.module_name: str = module_name
        self.is_type_checking: bool = is_type_checking
        self.from_items: str | None = from_items


def run_nested_import_check() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        _execute_hook_pipeline()
    except Exception as e:
        _handle_hook_error(e)


def detect_nested_import_violations(code: str) -> list[NestedImportIssue]:
    """Detect all nested import violations in the given code."""
    root: sg.SgRoot = sg.SgRoot(code, "python")
    node: sg.SgNode = root.root()
    source_lines: list[str] = code.split("\n")

    violations: list[NestedImportIssue] = []

    import_violations: list[NestedImportIssue] = _detect_import_statements(node, source_lines)
    violations.extend(import_violations)

    from_import_violations: list[NestedImportIssue] = _detect_from_import_statements(node, source_lines)
    violations.extend(from_import_violations)

    filtered_violations: list[NestedImportIssue] = [
        violation for violation in violations if not violation["is_type_checking"]
    ]
    return filtered_violations


def build_error_message(violations: list[NestedImportIssue], file_path: str) -> str:
    """Build error message for nested import violations."""
    if not violations:
        return ""

    display_path: str = _get_display_path(file_path)

    msg_parts: list[str] = []
    msg_parts.append("CRITICAL ERROR: NESTED IMPORT DETECTED - OPERATION BLOCKED\n")
    msg_parts.append("=" * 60 + "\n\n")
    msg_parts.append(f"File: {display_path}\n")
    msg_parts.append(f"Violations found: {len(violations)}\n\n")

    i: int
    violation: NestedImportIssue
    for i, violation in enumerate(violations, 1):
        msg_parts.append(f"[{i}] Line {violation['line']}: {violation['issue_description']}\n")
        msg_parts.append(f"\tProblem: {violation['text']}\n")
        msg_parts.append(f"\tSolution: {violation['suggestion']}\n\n")

    msg_parts.append("-" * 60 + "\n")
    msg_parts.append("This operation has been FORCEFULLY BLOCKED. Fix the issues above to proceed.\n")

    result: str = "".join(msg_parts)
    return result


def adjust_line_numbers_for_edit(
    violations: list[NestedImportIssue],
    file_path: str,
    tool_input: dict[str, Any],
) -> list[NestedImportIssue]:
    """Adjust line numbers for Edit tool based on position in file."""
    if not violations or not file_path or not Path(file_path).exists():
        return violations

    try:
        f: TextIO
        with open(file_path, encoding="utf-8") as f:
            full_content: str = f.read()

        old_string: str = tool_input.get("old_string", "")
        new_string: str = tool_input.get("new_string", "")

        index: int = full_content.find(old_string) if old_string else full_content.find(new_string)

        if index != -1:
            lines_before: int = full_content[:index].count("\n")
            violation: NestedImportIssue
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


def process_tool_input(data: InputData) -> list[NestedImportIssue]:
    """Process tool input and detect violations."""
    tool_name: str = data.get("tool_name", "")
    tool_input: Any = data.get("tool_input", {})

    if not isinstance(tool_input, dict):
        return []

    processors: dict[str, Callable[[dict[str, Any]], list[NestedImportIssue]]] = {
        "Write": _process_write_tool,
        "Edit": _process_edit_tool,
        "MultiEdit": _process_multiedit_tool,
    }

    processor: Callable[[dict[str, Any]], list[NestedImportIssue]] | None = processors.get(tool_name)
    result: list[NestedImportIssue] = processor(tool_input) if processor else []
    return result


def handle_findings(violations: list[NestedImportIssue], file_path: str) -> NoReturn:
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
    violations: list[NestedImportIssue] = process_tool_input(data)
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

    return False


def _process_write_tool(tool_input: dict[str, Any]) -> list[NestedImportIssue]:
    """Process Write tool input."""
    content: str = tool_input.get("content", "")
    result: list[NestedImportIssue] = detect_nested_import_violations(content) if content else []
    return result


def _process_edit_tool(tool_input: dict[str, Any]) -> list[NestedImportIssue]:
    """Process Edit tool input."""
    new_string: str = tool_input.get("new_string", "")
    if not new_string:
        return []

    violations: list[NestedImportIssue] = detect_nested_import_violations(new_string)
    file_path: str = tool_input.get("file_path", "")
    adjusted_violations: list[NestedImportIssue] = adjust_line_numbers_for_edit(violations, file_path, tool_input)
    return adjusted_violations


def _process_multiedit_tool(tool_input: dict[str, Any]) -> list[NestedImportIssue]:
    """Process MultiEdit tool input."""
    violations: list[NestedImportIssue] = []
    edits: list[Any] = tool_input.get("edits", [])

    edit: Any
    for edit in edits:
        if isinstance(edit, dict):
            new_string: str = edit.get("new_string", "")
            if new_string:
                detected_violations: list[NestedImportIssue] = detect_nested_import_violations(new_string)
                violations.extend(detected_violations)

    return violations


def _detect_import_statements(node: sg.SgNode, source_lines: list[str]) -> list[NestedImportIssue]:
    """Detect regular import statements inside functions."""
    violations: list[NestedImportIssue] = []

    import_nodes: list[sg.SgNode] = node.find_all(pattern="import $MODULE")

    import_node: sg.SgNode
    for import_node in import_nodes:
        parent_function: sg.SgNode | None = _find_parent_function(import_node)
        if parent_function:
            context: ImportContext = ImportContext(
                import_type="import",
                import_node=import_node,
                function_name=_extract_function_name(parent_function),
                module_name=_extract_module_from_import(import_node),
                is_type_checking=_is_type_checking_import(import_node, source_lines),
                from_items=None,
            )
            issue: NestedImportIssue = _create_nested_import_issue(context)
            violations.append(issue)

    return violations


def _detect_from_import_statements(node: sg.SgNode, source_lines: list[str]) -> list[NestedImportIssue]:
    """Detect from...import statements inside functions."""
    violations: list[NestedImportIssue] = []

    from_import_nodes: list[sg.SgNode] = node.find_all(pattern="from $MODULE import $$$ITEMS")

    from_import_node: sg.SgNode
    for from_import_node in from_import_nodes:
        parent_function: sg.SgNode | None = _find_parent_function(from_import_node)
        if parent_function:
            context: ImportContext = ImportContext(
                import_type="from_import",
                import_node=from_import_node,
                function_name=_extract_function_name(parent_function),
                module_name=_extract_module_from_from_import(from_import_node),
                is_type_checking=_is_type_checking_import(from_import_node, source_lines),
                from_items=_extract_items_from_from_import(from_import_node),
            )
            issue: NestedImportIssue = _create_nested_import_issue(context)
            violations.append(issue)

    return violations


def _create_nested_import_issue(context: ImportContext) -> NestedImportIssue:
    """Create a NestedImportIssue object from context."""
    start: Any = context.import_node.range().start
    end: Any = context.import_node.range().end

    issue_description: str
    suggestion: str

    if context.import_type == "import":
        issue_description = f"Import '{context.module_name}' inside function '{context.function_name}'"
        suggestion = f"Move 'import {context.module_name}' to the top of the file"
    else:
        issue_description = f"Import from '{context.module_name}' inside function '{context.function_name}'"
        suggestion = f"Move 'from {context.module_name} import {context.from_items}' to the top of the file"

    issue: NestedImportIssue = NestedImportIssue(
        type=context.import_type,
        issue_description=issue_description,
        suggestion=suggestion,
        line=start.line + 1,
        column=start.column,
        end_line=end.line + 1,
        end_column=end.column,
        function_name=context.function_name,
        module_name=context.module_name,
        text=_truncate_text(context.import_node.text(), Config.DEFAULT_TEXT_TRUNCATION),
        is_type_checking=context.is_type_checking,
        from_items=context.from_items,
    )
    return issue


def _find_parent_function(node: sg.SgNode) -> sg.SgNode | None:
    """Find the parent function of a node."""
    current: sg.SgNode | None = node.parent()
    while current:
        if current.kind() == "function_definition":
            return current
        current = current.parent()
    return None


def _extract_function_name(function_node: sg.SgNode) -> str:
    """Extract function name from a function node."""
    name_node: sg.SgNode | None = function_node.field("name")
    if name_node:
        return name_node.text()
    return "unknown"


def _extract_module_from_import(import_node: sg.SgNode) -> str:
    """Extract module name from import statement."""
    module_match: sg.SgNode | None = import_node.get_match("MODULE")
    if module_match:
        return module_match.text()
    return "unknown"


def _extract_module_from_from_import(from_import_node: sg.SgNode) -> str:
    """Extract module name from from...import statement."""
    module_match: sg.SgNode | None = from_import_node.get_match("MODULE")
    if module_match:
        return module_match.text()
    return "unknown"


def _extract_items_from_from_import(from_import_node: sg.SgNode) -> str:
    """Extract imported items from from...import statement."""
    items_matches: list[sg.SgNode] = from_import_node.get_multiple_matches("ITEMS")
    if items_matches:
        items_text: list[str] = [item.text() for item in items_matches]
        return "".join(items_text)
    return "unknown"


def _is_type_checking_import(import_node: sg.SgNode, source_lines: list[str]) -> bool:
    """Check if import is inside TYPE_CHECKING block or has # type: ignore comment."""
    import_line_num: int = import_node.range().start.line
    if import_line_num < len(source_lines):
        import_line: str = source_lines[import_line_num]
        if TYPE_IGNORE_PATTERN.search(import_line):
            return True

    current: sg.SgNode | None = import_node.parent()
    while current:
        if current.kind() == "if_statement":
            condition_node: sg.SgNode | None = current.field("condition")
            if condition_node:
                condition_text: str = condition_node.text()
                if "TYPE_CHECKING" in condition_text:
                    return True
        current = current.parent()

    return False


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
    run_nested_import_check()
