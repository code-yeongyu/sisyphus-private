#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Curl command blocker hook for Claude Code.
Blocks Bash commands that use curl and suggests HTTPie as an alternative.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import traceback
from collections.abc import Callable
from re import Pattern
from typing import NoReturn, NotRequired, TypedDict

sys.exit(0)  # DISABLED: curl is actually faster, has more features than httpie


class Config:
    """Configuration constants for curl blocker."""

    EXIT_CODE_BLOCK_TOOL: int = 2
    CURL_PATTERN: Pattern[str] = re.compile(r"\b(?:curl|CURL)\b(?:\s|$|;|\||&)", re.IGNORECASE | re.MULTILINE)


# Type definitions
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


# Main entry point
def run_curl_check() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        execute_hook_pipeline()
    except Exception as e:
        _handle_hook_error(e)


# Pipeline execution
def execute_hook_pipeline() -> None:
    """Execute the main hook logic pipeline."""
    data: InputData = parse_input()

    if not should_process(data):
        sys.exit(0)

    command: str = extract_command(data)
    has_curl = bool(command) and detect_curl_usage(command)
    handle_findings(has_curl, command)


# Input processing functions
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


# Curl detection functions
def detect_curl_usage(command: str) -> bool:
    """Detect if the command contains curl."""
    return bool(Config.CURL_PATTERN.search(command))


def convert_curl_to_httpie(command: str) -> str:
    """Convert curl command to HTTPie using available converters."""
    curl_cmd = _extract_curl_command(command)
    if not curl_cmd:
        return ""

    for converter in _get_converter_strategies():
        try:
            result = converter(curl_cmd)
            if result:
                return result
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            continue

    return ""


# Output handling functions
def handle_findings(has_curl: bool, command: str) -> NoReturn:
    """Handle detected curl usage and exit appropriately."""
    if not has_curl:
        sys.exit(0)

    message: str = build_error_message(command)
    print(message, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_BLOCK_TOOL)


def build_error_message(command: str) -> str:
    """Build error message for curl usage."""
    httpie_command = convert_curl_to_httpie(command)

    pipe_to_bash = "| bash" in command or "| sh" in command or "|bash" in command or "|sh" in command

    if pipe_to_bash:
        return """CURL BLOCKED - SECURITY WARNING

⚠️  Piping scripts directly to bash is dangerous!
Instead, download and review the script first:

```sh
# Download and review
http --download https://example.com/install.sh
cat install.sh  # Review the script
bash install.sh  # Run if safe
```

For HTTPie, use --download or --print=b for raw output."""
    elif httpie_command:
        return f"""CURL BLOCKED

Use instead:

```sh
{httpie_command}
```

Note: HTTPie outputs JSON by default. For raw text use --print=b"""
    else:
        return """CURL BLOCKED

Use HTTPie instead. Example:

```sh
http GET https://api.example.com
```"""


# Private helper functions
def _extract_curl_command(command: str) -> str:
    """Extract curl command from the full command string."""
    curl_match = re.search(r"(curl\s+[^;&|]+)", command, re.IGNORECASE)
    return curl_match.group(1) if curl_match else ""


def _try_bunx_converter(curl_cmd: str) -> str:
    """Try converting curl to HTTPie using bunx."""
    result = subprocess.run(
        ["bunx", "--bun", "curlconverter", "--language", "httpie", "-"],
        check=False,
        input=curl_cmd,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _try_curlconverter(curl_cmd: str) -> str:
    """Try converting curl to HTTPie using curlconverter directly."""
    result = subprocess.run(
        ["curlconverter", "--language", "httpie", "-"],
        check=False,
        input=curl_cmd,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _get_converter_strategies() -> list[Callable[[str], str]]:
    """Get list of converter strategies to try."""
    return [_try_bunx_converter, _try_curlconverter]


def _handle_hook_error(e: Exception) -> NoReturn:
    """Handle errors in hook execution."""
    print(f"ERROR in hook: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    run_curl_check()
