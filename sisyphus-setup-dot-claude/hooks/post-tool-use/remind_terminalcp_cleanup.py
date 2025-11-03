#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false
"""
Remind about terminalcp cleanup after usage (PostToolUse).

This hook reminds Claude to clean up terminalcp processes after using them,
preventing resource leaks from background processes.
"""

from __future__ import annotations

import json
import sys
from typing import Any, NoReturn


class Config:
    EXIT_CODE_INFORM: int = 2


CLEANUP_REMINDER_MESSAGE = """[terminalcp-cleanup-reminder]

REMINDER: You are working with terminalcp background processes.

**CRITICAL: Always clean up processes when done**

To stop a specific process:
terminalcp stop <process-id>

To stop all processes:
terminalcp stop

To list active processes:
terminalcp list

Failing to clean up processes will cause resource leaks!
"""


def main() -> None:
    try:
        execute_hook_pipeline()
    except Exception:
        handle_hook_error()


def execute_hook_pipeline() -> None:
    data = parse_input()

    if not should_process(data):
        sys.exit(0)

    handle_findings()


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
    if tool_name != "Bash":
        return False

    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return False

    command = tool_input.get("command", "")
    if not isinstance(command, str):
        return False

    if "terminalcp" not in command:
        return False

    return "terminalcp start" in command


def handle_findings() -> NoReturn:
    print(CLEANUP_REMINDER_MESSAGE, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_INFORM)


def handle_hook_error() -> NoReturn:
    sys.exit(0)


if __name__ == "__main__":
    main()
