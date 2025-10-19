#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Remind about tmux usage for interactive operations (PostToolUse).

This hook suggests using tmux for interactive shells, debuggers, TUI apps,
and other terminal-based tools when Bash commands are executed.
"""

from __future__ import annotations

import json
import sys
from typing import Any, NoReturn


class Config:
    EXIT_CODE_INFORM: int = 2
    SESSION_PREFIX: str = "claude-code-"


TMUX_USAGE_MESSAGE = """[interactive-bash-operations]

When working with interactive operations, consider using tmux:

**Use cases:**
- Debugging (pdb, gdb, lldb)
- TUI applications (ccc, htop, vim, nvim)
- Interactive git (git rebase -i, git add -p)
- REPL environments (python -i, node, irb)
- Long-running processes

**Quick start:**
# Start session
tmux new-session -d -s claude-code-{name} 'command'

# Send input
tmux send-keys -t claude-code-{name} 'text' Enter

# Capture output
tmux capture-pane -t claude-code-{name} -p

# Clean up (CRITICAL!)
tmux kill-session -t claude-code-{name}

BUT ONLY USE THESE ONLY WHEN INTERACTIVE ARE REQUIRED. FOR NORMAL CASES JUST USE Bash TOOL.
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

    return not command.strip().startswith("tmux")


def handle_findings() -> NoReturn:
    print(TMUX_USAGE_MESSAGE, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_INFORM)


def handle_hook_error() -> NoReturn:
    sys.exit(0)


if __name__ == "__main__":
    main()
