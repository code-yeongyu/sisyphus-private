#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Grep command blocker hook for Claude Code.
Blocks Bash commands that use grep and suggests ripgrep (rg) as an alternative.
"""

from __future__ import annotations

import json
import re
import sys
import traceback
from re import Pattern
from typing import NoReturn, NotRequired, TypedDict


class Config:
    """Configuration constants for grep blocker."""

    EXIT_CODE_BLOCK_TOOL: int = 2
    GREP_PATTERN: Pattern[str] = re.compile(
        r"\b(?:grep|GREP|egrep|EGREP|fgrep|FGREP)\b(?:\s|$|;|\||&)",
        re.IGNORECASE | re.MULTILINE,
    )


class BashToolInput(TypedDict):
    command: str
    description: NotRequired[str]
    timeout: NotRequired[int]
    run_in_background: NotRequired[bool]


class InputData(TypedDict):
    session_id: NotRequired[str]
    transcript_path: NotRequired[str]
    cwd: NotRequired[str]
    hook_event_name: NotRequired[str]
    tool_name: NotRequired[str]
    tool_input: NotRequired[BashToolInput]


def run_grep_check() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        execute_hook_pipeline()
    except Exception as e:
        _handle_hook_error(e)


def execute_hook_pipeline() -> None:
    """Execute the main hook logic pipeline."""
    data: InputData = parse_input()

    if not should_process(data):
        sys.exit(0)

    command: str = extract_command(data)
    has_grep = bool(command) and detect_grep_usage(command)
    handle_findings(has_grep, command)


def parse_input() -> InputData:
    """Parse and validate stdin input."""
    input_raw: str = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        parsed_data: InputData = json.loads(input_raw)
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON input: {e}", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error parsing input: {e}", file=sys.stderr)
        sys.exit(0)


def should_process(data: InputData) -> bool:
    """Determine if the input should be processed."""
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input")

    return tool_name == "Bash" and isinstance(tool_input, dict) and bool(tool_input.get("command"))


def extract_command(data: InputData) -> str:
    """Extract command from input data."""
    tool_input = data.get("tool_input")
    if isinstance(tool_input, dict):
        return tool_input.get("command", "")
    return ""


def detect_grep_usage(command: str) -> bool:
    """Detect if the command contains grep."""
    return bool(Config.GREP_PATTERN.search(command))


def handle_findings(has_grep: bool, command: str) -> NoReturn:
    """Handle detected grep usage and exit appropriately."""
    if not has_grep:
        sys.exit(0)

    message: str = build_error_message()
    print(message, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_BLOCK_TOOL)


def build_error_message() -> str:
    """Build error message for grep usage."""
    return """GREP BLOCKED

Great choice using grep! It's an excellent and powerful tool that we absolutely love.
However, in this development environment, we need to use rg (ripgrep) instead.
Please continue with what you were trying to do, but use rg instead of grep.
Don't resort to other tools like tail, head, or cat - just use rg for your search needs.

Note: ripgrep uses extended regex by default, so:
- Use `|` for OR (not `\\|` like in basic grep)
- No need to escape special characters like grep -E
- Example: `rg "pattern1|pattern2"` instead of `grep "pattern1\\|pattern2"`"""


def _handle_hook_error(e: Exception) -> NoReturn:
    """Handle errors in hook execution."""
    print(f"ERROR in hook: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    run_grep_check()
