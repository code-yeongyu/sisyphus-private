#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false, reportUnknownArgumentType=false

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any, TypedDict

UNCOMPILED_RE_FUNCTIONS = {
    "match",
    "search",
    "findall",
    "finditer",
    "sub",
    "subn",
    "split",
    "fullmatch",
}


def main() -> None:
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    try:
        input_raw: str = sys.stdin.read()
        if not input_raw:
            print(f"[{hook_filename}] Skipping: No input provided", file=sys.stderr)
            sys.exit(0)

        data: PostToolUseInput = json.loads(input_raw)
    except (json.JSONDecodeError, KeyError, TypeError):
        print(f"[{hook_filename}] Skipping: Invalid input format", file=sys.stderr)
        sys.exit(0)

    tool_name = data["tool_name"]
    tool_input = data["tool_input"]

    if not isinstance(tool_input, dict):
        print(f"[{hook_filename}] Skipping: Invalid tool input", file=sys.stderr)
        sys.exit(0)

    file_path: str = ""
    if "file_path" in tool_input:
        file_path = tool_input["file_path"]

    if not file_path:
        print(f"[{hook_filename}] Skipping: No file path provided", file=sys.stderr)
        sys.exit(0)

    if not file_path.endswith(".py"):
        print(f"[{hook_filename}] Skipping: Not a Python file", file=sys.stderr)
        sys.exit(0)

    all_findings: list[tuple[str, int, str, str]] = []

    try:
        match tool_name:
            case "Write":
                content = tool_input.get("content", "")
                if content:
                    findings = check_uncompiled_regex(content, file_path)
                    all_findings.extend(findings)

            case "Edit":
                new_string = tool_input.get("new_string", "")
                if new_string:
                    findings = check_uncompiled_regex(new_string, file_path)
                    all_findings.extend(findings)

            case "MultiEdit":
                edits = tool_input.get("edits", [])
                for edit in edits:
                    if isinstance(edit, dict):
                        new_string = edit.get("new_string", "")
                        if new_string:
                            findings = check_uncompiled_regex(new_string, file_path)
                            all_findings.extend(findings)

            case _:
                pass

    except Exception:
        print(f"[{hook_filename}] Skipping: Error during check", file=sys.stderr)
        sys.exit(0)

    if not all_findings:
        print(f"[{hook_filename}] Success: No uncompiled regex usage detected", file=sys.stderr)
        sys.exit(0)

    message = build_error_message(all_findings, file_path)
    print(f"\n{message}", file=sys.stderr)
    sys.exit(2)


def check_uncompiled_regex(content: str, file_path: str) -> list[tuple[str, int, str, str]]:
    """
    Check for uncompiled regex patterns in Python code.

    Returns list of (file_path, line_number, function_name, pattern) tuples.
    """
    findings: list[tuple[str, int, str, str]] = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return findings

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if not isinstance(node.func, ast.Attribute):
            continue

        if not isinstance(node.func.value, ast.Name):
            continue

        if node.func.value.id != "re":
            continue

        func_name = node.func.attr

        if func_name not in UNCOMPILED_RE_FUNCTIONS:
            continue

        if not node.args:
            continue

        pattern_arg = node.args[0]
        pattern_repr = ast.unparse(pattern_arg) if hasattr(ast, "unparse") else "<pattern>"

        line_no = node.lineno
        findings.append((file_path, line_no, func_name, pattern_repr))

    return findings


def build_error_message(findings: list[tuple[str, int, str, str]], file_path: str) -> str:
    """Build error message for uncompiled regex usage."""
    cwd = Path.cwd()

    try:
        path_obj = Path(file_path).resolve()
        if path_obj.is_relative_to(cwd):
            display_path = str(path_obj.relative_to(cwd))
        else:
            display_path = file_path
    except (ValueError, OSError):
        display_path = file_path

    violations_list = f"File: {display_path}\n"
    for _, line, func_name, pattern in findings:
        violations_list += f"  Line {line}: re.{func_name}({pattern}, ...)\n"

    msg = "UNCOMPILED REGEX DETECTED - PERFORMANCE ISSUE\n\n"
    msg += "Your code uses re.match/search/findall/sub/split without pre-compiling the regex.\n"
    msg += "This is inefficient when the same pattern is used multiple times.\n\n"
    msg += "RECOMMENDED ACTION:\n\n"
    msg += "1. If the pattern is used multiple times:\n"
    msg += "   → Compile it once at module level or class level\n"
    msg += "   → Example:\n"
    msg += "     ```python\n"
    msg += "     # Bad\n"
    msg += "     result = re.match(r'\\d+', text)\n\n"
    msg += "     # Good\n"
    msg += "     DIGIT_PATTERN = re.compile(r'\\d+')\n"
    msg += "     result = DIGIT_PATTERN.match(text)\n"
    msg += "     ```\n\n"
    msg += "2. If the pattern is truly used only once:\n"
    msg += "   → Acknowledge this warning and explain why it's acceptable\n"
    msg += "   → Example: Dynamic patterns, one-time validation\n\n"
    msg += "3. For Config classes with regex patterns:\n"
    msg += "   → ALWAYS use class-level compiled patterns\n"
    msg += "   → Example:\n"
    msg += "     ```python\n"
    msg += "     class Config:\n"
    msg += "         PATTERN = re.compile(r'...')\n"
    msg += "     ```\n\n"
    msg += "PERFORMANCE IMPACT:\n"
    msg += "- Compiling regex is expensive (parsing, optimization)\n"
    msg += "- Using pre-compiled patterns is 2-10x faster for repeated use\n"
    msg += "- Module-level compilation happens once at import time\n\n"
    msg += "Detected uncompiled regex usage:\n"
    msg += violations_list

    return msg


class PostToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: dict[str, Any]
    tool_response: dict[str, Any]


if __name__ == "__main__":
    main()
