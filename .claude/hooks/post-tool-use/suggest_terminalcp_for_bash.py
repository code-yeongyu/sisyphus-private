#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NotRequired, TypedDict


class PostToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: dict[str, Any]
    tool_response: dict[str, Any]


class TranscriptMessage(TypedDict):
    role: NotRequired[str]
    content: NotRequired[str | list[dict[str, Any]]]


TERMINALCP_IDENTIFIER = "[terminalcp-suggestion-shown]"


def is_suggestion_already_shown(transcript_path: str) -> bool:
    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        return False

    try:
        with transcript_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    message: TranscriptMessage = json.loads(line)
                    content = message.get("content", "")

                    if isinstance(content, list):
                        content_str = json.dumps(content)
                    else:
                        content_str = str(content)

                    if TERMINALCP_IDENTIFIER in content_str:
                        return True

                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

        return False

    except OSError:
        return False


def main() -> None:
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    try:
        input_raw = sys.stdin.read()
        if not input_raw:
            print(f"[{hook_filename}] Skipping: No input provided")
            sys.exit(0)

        data: PostToolUseInput = json.loads(input_raw)
    except (json.JSONDecodeError, KeyError, TypeError):
        print(f"[{hook_filename}] Skipping: Invalid input format")
        sys.exit(0)

    tool_name = data["tool_name"]

    if tool_name != "Bash":
        print(f"[{hook_filename}] Skipping: Tool {tool_name} is not Bash")
        sys.exit(0)

    transcript_path = data["transcript_path"]

    if is_suggestion_already_shown(transcript_path):
        print(f"[{hook_filename}] Skipping: Suggestion already shown in this session")
        sys.exit(0)

    message = f"""{TERMINALCP_IDENTIFIER}
Note: For interactive operations, consider using `terminalcp` instead of Bash

terminalcp provides better support for:
- Interactive processes, TUI Applications
    - REPL
    - Debuggers
    - ...
- Long-running background processes
- Stdin/stdout interaction with proper terminal emulation
- Session management and monitoring

Example usage:
- Start session: mcp__terminalcp__terminalcp with action="start"
- Send input: action="stdin" with data (supports escape sequences)
- Get output: action="stdout" for rendered view, action="stream" for raw output
- Manage: action="list" to see all sessions, action="stop" to terminate
"""

    print(message, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
