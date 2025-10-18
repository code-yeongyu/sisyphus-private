#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict


class PostToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: dict[str, Any]
    tool_response: dict[str, Any]


def main() -> None:
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    try:
        input_raw = sys.stdin.read()
        if not input_raw:
            print(f"[{hook_filename}] Skipping: No input provided")
            sys.exit(0)

        data: PostToolUseInput = json.loads(input_raw)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[{hook_filename}] Skipping: Invalid input format: {e}")
        sys.exit(0)

    tool_name = data["tool_name"]

    if tool_name != "mcp__terminalcp__terminalcp":
        print(f"[{hook_filename}] Skipping: Tool {tool_name} is not terminalcp")
        sys.exit(0)

    tool_input = data["tool_input"]

    args = tool_input.get("args", {})
    action = args.get("action")

    if action != "start":
        print(f"[{hook_filename}] Skipping: Action {action} is not 'start'")
        sys.exit(0)

    session_id = args.get("id", args.get("name", "unknown"))
    command = args.get("command", "")  # noqa: F841

    try:
        result = subprocess.run(
            ["npx", "-y", "terminalcp", "list"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(
                f"[{hook_filename}] Warning: terminalcp list failed with code {result.returncode}"
            )
            sys.exit(0)

        output = result.stdout.strip()

        message = f"""[terminalcp-session-started]
Just created terminalcp session '{session_id}'.

IMPORTANT: Don't forget to terminate the session when done using action="stop"!
Current active sessions:
{output}


MUST DO ACTION: TELL THE USER THAT they can attach to this session using CLI:

```sh
terminalcp attach {session_id}
```
"""

        print(message, file=sys.stderr)
        sys.exit(2)

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[{hook_filename}] Error running terminalcp list: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
