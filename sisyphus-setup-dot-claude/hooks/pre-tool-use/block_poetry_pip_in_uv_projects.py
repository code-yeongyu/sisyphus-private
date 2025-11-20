#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false
"""
Poetry/Pip blocker for UV projects (PreToolUse hook).
Detects UV projects and blocks poetry/pip commands, suggesting uv alternatives.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import NoReturn, NotRequired, TypedDict


class Config:
    """Configuration constants for UV guard."""

    EXIT_CODE_BLOCK_TOOL: int = 2

    POETRY_PATTERN: re.Pattern[str] = re.compile(r"\bpoetry\b", re.IGNORECASE)
    PIP_PATTERN: re.Pattern[str] = re.compile(r"\b(?:pip|python\s+-m\s+pip)\b", re.IGNORECASE)

    ALLOWED_PIP_COMMANDS = {
        "pip list",
        "pip show",
        "pip freeze",
        "pip --version",
        "pip -V",
        "python -m pip list",
        "python -m pip show",
        "python -m pip freeze",
        "python -m pip --version",
    }


class BashToolInput(TypedDict):
    command: str
    description: NotRequired[str]
    timeout: NotRequired[int]
    run_in_background: NotRequired[bool]


class PreToolUseInput(TypedDict):
    session_id: NotRequired[str]
    transcript_path: NotRequired[str]
    cwd: NotRequired[str]
    hook_event_name: NotRequired[str]
    tool_name: NotRequired[str]
    tool_input: NotRequired[BashToolInput]


class DetectionResult(TypedDict):
    detected: bool
    package_manager: str
    original_command: str
    suggested_command: str


def main() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        execute_hook_pipeline()
    except Exception:
        handle_hook_error()


def execute_hook_pipeline() -> None:
    """Execute the main hook logic pipeline."""
    data: PreToolUseInput = parse_input()

    if not should_process(data):
        sys.exit(0)

    command: str = extract_command(data)
    cwd: str = data.get("cwd", "")

    if not cwd or not command:
        sys.exit(0)

    target_dir = extract_target_directory(command, Path(cwd))

    if not is_uv_project(target_dir):
        sys.exit(0)

    result = detect_package_manager_usage(command)
    handle_findings(result)


def parse_input() -> PreToolUseInput:
    """Parse and validate stdin input."""
    input_raw: str = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        parsed_data: PreToolUseInput = json.loads(input_raw)
        return parsed_data
    except json.JSONDecodeError:
        sys.exit(0)


def should_process(data: PreToolUseInput) -> bool:
    """Determine if the input should be processed."""
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input")

    return tool_name == "Bash" and isinstance(tool_input, dict) and bool(tool_input.get("command"))


def extract_command(data: PreToolUseInput) -> str:
    """Extract command from input data."""
    tool_input = data.get("tool_input")
    if isinstance(tool_input, dict):
        return tool_input.get("command", "")
    return ""


def extract_target_directory(command: str, cwd: Path) -> Path:
    """
    Extract target directory from command, considering cd commands.

    If command contains 'cd <path> &&' or 'cd <path>;', extracts the last cd target.
    Resolves relative paths against cwd.

    Examples:
    - "cd /tmp && poetry install" → /tmp
    - "cd subdir && pip install X" → cwd/subdir
    - "poetry install" → cwd
    """
    cd_pattern = re.compile(r"\bcd\s+([^\s;&|]+)\s*(?:&&|;)", re.IGNORECASE)
    matches = cd_pattern.findall(command)

    if not matches:
        return cwd

    last_cd_target = matches[-1].strip()

    last_cd_target = last_cd_target.strip('"').strip("'")

    try:
        target = Path(last_cd_target)
        if target.is_absolute():
            return target.resolve()
        else:
            return (cwd / target).resolve()
    except (ValueError, OSError):
        return cwd


def is_uv_project(cwd: Path) -> bool:
    """
    Detect if the current directory is a UV project.

    Checks for:
    1. uv.lock file (definitive indicator)
    2. pyproject.toml with [tool.uv] section
    3. .python-version file (UV creates this)

    Searches from cwd up to root, stopping at common project markers.
    """
    current = cwd.resolve()

    max_depth = 10
    for _ in range(max_depth):
        if (current / "uv.lock").exists():
            return True

        pyproject_toml = current / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                content = pyproject_toml.read_text()
                if "[tool.uv]" in content or "tool.uv" in content:
                    return True

                if "[tool.poetry]" in content or "tool.poetry" in content:
                    return False

            except (OSError, UnicodeDecodeError):
                pass

        if (current / ".python-version").exists() and (current / "pyproject.toml").exists():
            return True

        if any((current / marker).exists() for marker in [".git", ".hg", ".svn"]):
            return False

        parent = current.parent
        if parent == current:
            break
        current = parent

    return False


def detect_package_manager_usage(command: str) -> DetectionResult:
    """
    Detect if command uses poetry/pip and suggest UV alternative.

    Handles chained commands (&&, ;, |) by checking each part.

    Returns DetectionResult with detection status and suggested command.
    """
    parts = re.split(r"(\s*(?:&&|;|\|)\s*)", command)

    for _i, part in enumerate(parts):
        if re.match(r"^\s*(?:&&|;|\|)\s*$", part):
            continue

        cmd_part = part.strip()
        if not cmd_part:
            continue

        is_allowed = False
        for allowed_cmd in Config.ALLOWED_PIP_COMMANDS:
            if allowed_cmd in cmd_part.lower():
                is_allowed = True
                break

        if is_allowed:
            continue

        if Config.POETRY_PATTERN.search(cmd_part):
            suggested = convert_to_uv(command, "poetry")
            return DetectionResult(
                detected=True,
                package_manager="poetry",
                original_command=command,
                suggested_command=suggested,
            )

        if Config.PIP_PATTERN.search(cmd_part):
            suggested = convert_to_uv(command, "pip")
            return DetectionResult(
                detected=True,
                package_manager="pip",
                original_command=command,
                suggested_command=suggested,
            )

    return DetectionResult(
        detected=False,
        package_manager="",
        original_command=command,
        suggested_command="",
    )


def convert_to_uv(command: str, package_manager: str) -> str:
    """
    Convert poetry/pip command to UV equivalent.

    Examples:
    - poetry install → uv sync
    - poetry add requests → uv add requests
    - poetry run pytest → uv run pytest
    - pip install requests → uv add requests
    - python -m pip install X → uv add X
    """
    if package_manager == "poetry":
        result = command

        result = re.sub(r"\bpoetry\s+install\b", "uv sync", result, flags=re.IGNORECASE)
        result = re.sub(r"\bpoetry\s+add\b", "uv add", result, flags=re.IGNORECASE)
        result = re.sub(r"\bpoetry\s+remove\b", "uv remove", result, flags=re.IGNORECASE)
        result = re.sub(r"\bpoetry\s+run\b", "uv run", result, flags=re.IGNORECASE)
        result = re.sub(r"\bpoetry\s+update\b", "uv sync --upgrade", result, flags=re.IGNORECASE)
        result = re.sub(r"\bpoetry\s+lock\b", "uv lock", result, flags=re.IGNORECASE)

        if result == command:
            result = re.sub(r"\bpoetry\b", "uv", result, flags=re.IGNORECASE)

        return result

    if package_manager == "pip":
        result = command

        result = re.sub(
            r"\bpython\s+-m\s+pip\s+install\s+",
            "uv add ",
            result,
            flags=re.IGNORECASE,
        )
        result = re.sub(r"\bpip\s+install\s+", "uv add ", result, flags=re.IGNORECASE)

        result = re.sub(
            r"\bpython\s+-m\s+pip\s+uninstall\s+",
            "uv remove ",
            result,
            flags=re.IGNORECASE,
        )
        result = re.sub(r"\bpip\s+uninstall\s+", "uv remove ", result, flags=re.IGNORECASE)

        if result == command:
            result = re.sub(r"\bpython\s+-m\s+pip\b", "uv", result, flags=re.IGNORECASE)
            result = re.sub(r"\bpip\b", "uv", result, flags=re.IGNORECASE)

        return result

    return command


def handle_findings(result: DetectionResult) -> NoReturn:
    """Handle detection results and exit appropriately."""
    if not result["detected"]:
        sys.exit(0)

    message: str = build_error_message(result)
    print(message, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_BLOCK_TOOL)


def build_error_message(result: DetectionResult) -> str:
    """Build error message suggesting UV alternative."""
    pm = result["package_manager"]
    original = result["original_command"]
    suggested = result["suggested_command"]

    return f"""🔒 UV PROJECT DETECTED - {pm.upper()} BLOCKED

This is a UV project (uv.lock or [tool.uv] detected).
Use UV instead of {pm} for better performance and consistency.

❌ Blocked command:
{original}

✅ Use this instead:
{suggested}

💡 Quick reference:
  poetry install → uv sync
  poetry add X   → uv add X
  poetry run cmd → uv run cmd
  pip install X  → uv add X
  pip uninstall  → uv remove X

Note: Read-only pip commands (list, show, freeze) are allowed.
"""


def handle_hook_error() -> NoReturn:
    """Handle errors in hook execution."""
    sys.exit(0)


if __name__ == "__main__":
    main()
