#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.12"
# dependencies = [
#     "orjson",
# ]
# ///
"""
Cleanup terminalcp sessions on SessionEnd hook.

Automatically stops terminalcp sessions that were created during the Claude Code
session when the session ends, preventing resource leaks from orphaned processes.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict

try:
    import orjson  # pyright: ignore[reportMissingImports]
except ImportError:
    orjson = None  # type: ignore[assignment]

TERMINALCP_START_PATTERN = re.compile(r"terminalcp\s+start\s+([^\s\"']+)")
TERMINALCP_ID_FLAG_PATTERN = re.compile(r"--id[=\s]+([^\s\"']+)")


class SessionEndInput(TypedDict):
    """SessionEnd hook input structure."""

    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: str
    hook_event_name: str
    reason: str  # "clear", "logout", "prompt_input_exit", "other"


def main() -> None:
    """Main entry point for SessionEnd hook."""
    try:
        data = parse_input()

        if not data:
            sys.exit(0)

        transcript_path = Path(data.get("transcript_path", ""))
        if not transcript_path.exists():
            sys.exit(0)

        # Extract terminalcp session IDs from transcript
        transcript_sessions = extract_terminalcp_sessions_from_transcript(transcript_path)

        if not transcript_sessions:
            sys.exit(0)

        # Get currently active terminalcp sessions
        active_sessions = get_active_terminalcp_sessions()

        if not active_sessions:
            sys.exit(0)

        # Find sessions to cleanup (created in this transcript AND still running)
        to_cleanup = [sid for sid in transcript_sessions if sid in active_sessions]

        if not to_cleanup:
            sys.exit(0)

        # Cleanup sessions
        cleaned = cleanup_terminalcp_sessions(to_cleanup)

        if cleaned:
            print(
                f"[terminalcp-cleanup] Stopped {len(cleaned)} session(s): {', '.join(cleaned)}",
                file=sys.stderr,
            )

    except Exception:
        # Silent failure - don't break session end
        pass

    sys.exit(0)


def parse_input() -> dict[str, Any]:
    """Parse SessionEnd hook input from stdin."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        return {}

    try:
        return json.loads(input_raw)
    except json.JSONDecodeError:
        return {}


def extract_terminalcp_sessions_from_transcript(transcript_path: Path) -> list[str]:
    """Extract terminalcp session IDs from transcript JSONL."""
    if orjson is None:
        return []

    session_ids = []

    try:
        with transcript_path.open("rb") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = orjson.loads(line)

                    # Only process assistant messages (tool calls)
                    if data.get("type") != "assistant":
                        continue

                    message = data.get("message", {})
                    content = message.get("content", [])

                    # Handle list of content items
                    if not isinstance(content, list):
                        continue

                    for item in content:
                        if not isinstance(item, dict):
                            continue

                        # Look for Bash tool use
                        if item.get("type") == "tool_use" and item.get("name") == "Bash":
                            tool_input = item.get("input", {})
                            command = tool_input.get("command", "")

                            # Parse terminalcp start commands
                            if "terminalcp start" in command:
                                session_id = parse_terminalcp_session_id(command)
                                if session_id:
                                    session_ids.append(session_id)

                except orjson.JSONDecodeError:
                    continue

    except OSError:
        return []

    return list(set(session_ids))  # Deduplicate


def parse_terminalcp_session_id(command: str) -> str | None:
    """
    Parse terminalcp session ID from command.

    Patterns:
    - terminalcp start <session-id> "command"
    - terminalcp start <session-id> command
    - terminalcp start --id=<session-id> "command"
    """
    # Pattern 1: terminalcp start <id> ...
    match = re.search(r"terminalcp\s+start\s+([^\s\"']+)", command)
    if match:
        session_id = match.group(1)
        # Skip if it's a flag
        if not session_id.startswith("-"):
            return session_id

    # Pattern 2: --id=<id>
    match = re.search(r"--id[=\s]+([^\s\"']+)", command)
    if match:
        return match.group(1)

    return None


def get_active_terminalcp_sessions() -> list[str]:
    """Get currently active terminalcp session IDs."""
    try:
        result = subprocess.run(["terminalcp", "list"], check=False, capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            return []

        # Parse output for session IDs
        # Format: "  session-id\n    Status: running\n..."
        session_ids = []
        for line in result.stdout.splitlines():
            stripped = line.strip()

            # Skip empty lines and known keywords
            if not stripped:
                continue

            if any(keyword in stripped for keyword in ["Status:", "CWD:", "Command:", "No active"]):
                continue

            # Session ID lines are not indented in original output, but appear as first line
            # After stripping, they're just the ID
            if not line.startswith(" " * 4):  # Check original indentation
                session_ids.append(stripped)

        return session_ids

    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return []


def cleanup_terminalcp_sessions(session_ids: list[str]) -> list[str]:
    """Stop terminalcp sessions. Returns list of successfully stopped sessions."""
    cleaned = []

    for session_id in session_ids:
        try:
            result = subprocess.run(
                ["terminalcp", "stop", session_id],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                cleaned.append(session_id)

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue

    return cleaned


if __name__ == "__main__":
    main()
