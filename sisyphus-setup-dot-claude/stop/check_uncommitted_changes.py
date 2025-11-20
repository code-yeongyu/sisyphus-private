#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.12"
# dependencies = []
# ///
"""
Stop hook that blocks Claude from stopping when uncommitted changes exist.

This hook checks git status and blocks if there are any uncommitted changes
in the current branch, informing Claude to commit them first.
"""

from __future__ import annotations

import datetime
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import NoReturn, TypedDict


class StopInput(TypedDict):
    """Input structure for Stop hook event."""

    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # Always "Stop"


class Config:
    """Configuration constants."""

    EXIT_CODE_ALLOW: int = 0
    EXIT_CODE_BLOCK: int = 2


def main() -> None:
    """Main entry point."""
    log_path = Path.home() / ".claude" / "hook_debug.log"
    try:
        with log_path.open("a", encoding="utf-8") as log_file:
            _ = log_file.write(f"\n=== Stop Hook (Uncommitted Changes Check) {datetime.datetime.now()} ===\n")
            input_data = sys.stdin.read()
            _ = log_file.write(f"Input: {input_data}\n")

        sys.stdin = io.StringIO(input_data)
        execute_hook_pipeline()
    except Exception as exception:
        with log_path.open("a", encoding="utf-8") as log_file:
            _ = log_file.write(f"Exception: {exception}\n")
        sys.exit(Config.EXIT_CODE_ALLOW)


def execute_hook_pipeline() -> None:
    """Execute the main hook logic pipeline."""
    data = parse_input()
    cwd = data.get("cwd", "")

    if not cwd:
        with open(Path.home() / ".claude" / "hook_debug.log", "a") as f:
            _ = f.write("No cwd provided\n")
        sys.exit(Config.EXIT_CODE_ALLOW)

    uncommitted_changes = check_uncommitted_changes(cwd)

    with open(Path.home() / ".claude" / "hook_debug.log", "a") as f:
        _ = f.write(f"CWD: {cwd}, Uncommitted changes: {bool(uncommitted_changes)}\n")
        if uncommitted_changes:
            _ = f.write(f"Changes:\n{uncommitted_changes}\n")

    handle_findings(uncommitted_changes)


def parse_input() -> StopInput:
    """Parse and validate stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(Config.EXIT_CODE_ALLOW)

    try:
        data = json.loads(input_raw)
        return data
    except json.JSONDecodeError:
        sys.exit(Config.EXIT_CODE_ALLOW)


def check_uncommitted_changes(cwd: str) -> str:
    """
    Check for uncommitted changes in the git repository.

    Args:
        cwd: Current working directory path

    Returns:
        Git status output if changes exist, empty string if clean
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        return result.stdout.strip()

    except Exception:
        return ""


def handle_findings(uncommitted_changes: str) -> NoReturn:
    """
    Handle findings and exit appropriately.

    If uncommitted changes exist, block stoppage and inform Claude.
    Otherwise, allow stoppage.

    Args:
        uncommitted_changes: Git status output
    """
    if not uncommitted_changes:
        sys.exit(Config.EXIT_CODE_ALLOW)

    response = {"decision": "block", "reason": build_error_message(uncommitted_changes)}
    print(json.dumps(response), file=sys.stdout)
    sys.exit(Config.EXIT_CODE_BLOCK)


def build_error_message(uncommitted_changes: str) -> str:
    """
    Build error message for Claude about uncommitted changes.

    Args:
        uncommitted_changes: Git status output

    Returns:
        Formatted error message
    """
    lines = [
        "",
        "You have uncommitted changes in the current branch:",
        "",
    ]

    for line in uncommitted_changes.split("\n"):
        if line.strip():
            lines.append(f"  {line}")

    lines.extend(
        [
            "",
            "Please commit all changes before stopping:",
            "  1. Review the changes",
            "  2. Stage files: git add <files>",
            '  3. Commit: git commit -m "<message>"',
            "",
            "YOU MUST COMMIT ALL CHANGES BEFORE STOPPING.",
        ]
    )

    return "\n".join(lines)


if __name__ == "__main__":
    main()
