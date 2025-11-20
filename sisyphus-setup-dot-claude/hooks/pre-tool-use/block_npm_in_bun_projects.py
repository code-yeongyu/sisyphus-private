#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false
"""
NPM/PNPM/Yarn blocker for Bun projects (PreToolUse hook).
Detects Bun projects and blocks npm/npx/pnpm/yarn commands, suggesting bun/bunx alternatives.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import NoReturn, NotRequired, TypedDict


class Config:
    """Configuration constants for Bun guard."""

    EXIT_CODE_BLOCK_TOOL: int = 2

    # Patterns to detect package managers
    NPM_PATTERN: re.Pattern[str] = re.compile(r"\b(npm|npx)\b", re.IGNORECASE)
    PNPM_PATTERN: re.Pattern[str] = re.compile(r"\bpnpm\b", re.IGNORECASE)
    YARN_PATTERN: re.Pattern[str] = re.compile(r"\byarn\b", re.IGNORECASE)

    # Global npm commands that should be allowed (publishing, authentication, etc.)
    ALLOWED_NPM_COMMANDS = {
        "npm publish",
        "npm login",
        "npm logout",
        "npm adduser",
        "npm owner",
        "npm access",
        "npm version",
        "npm deprecate",
        "npm unpublish",
        "npm dist-tag",
        "npm profile",
        "npm token",
        "npm whoami",
    }


# TypedDict definitions
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
    package_manager: str  # "npm", "npx", "pnpm", "yarn"
    original_command: str
    suggested_command: str


# Main entry point
def main() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        execute_hook_pipeline()
    except Exception:
        handle_hook_error()


# Pipeline execution
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

    if not is_bun_project(target_dir):
        sys.exit(0)

    result = detect_package_manager_usage(command)
    handle_findings(result)


# Input processing functions
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
    - "cd /tmp && npm install" → /tmp
    - "cd subdir && npm run build" → cwd/subdir
    - "npm install" → cwd
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


# Bun project detection
def is_bun_project(cwd: Path) -> bool:
    """
    Detect if the current directory is a Bun project.

    Checks for:
    1. bun.lockb file (definitive indicator)
    2. package.json with packageManager field containing "bun@"

    Searches from cwd up to root, stopping at common project markers.
    """
    current = cwd.resolve()

    # Search up to 10 levels or until we hit root
    max_depth = 10
    for _ in range(max_depth):
        # Check for bun.lockb (most reliable)
        if (current / "bun.lockb").exists():
            return True

        # Check package.json for packageManager field
        package_json = current / "package.json"
        if package_json.exists():
            try:
                with package_json.open() as f:
                    data = json.load(f)
                    package_manager = data.get("packageManager", "")
                    if "bun@" in package_manager:
                        return True

                    # If package.json exists but no bun indicator, stop searching
                    # (assume this is the project root with different package manager)
                    if "packageManager" in data:
                        return False

            except (json.JSONDecodeError, OSError):
                pass

        # Stop at git root or other project markers
        if any((current / marker).exists() for marker in [".git", ".hg", ".svn"]):
            # Found version control root but no Bun indicators
            return False

        # Move up one directory
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    return False


# Package manager detection
def detect_package_manager_usage(command: str) -> DetectionResult:
    """
    Detect if command uses npm/npx/pnpm/yarn and suggest Bun alternative.

    Handles chained commands (&&, ;, |) by checking each part.

    Returns DetectionResult with detection status and suggested command.
    """
    # Split command by common separators (&&, ;, |) while preserving separators
    # This regex splits on &&, ;, or | but keeps the separator
    parts = re.split(r"(\s*(?:&&|;|\|)\s*)", command)

    # Check each command part for package manager usage
    for _i, part in enumerate(parts):
        # Skip separators
        if re.match(r"^\s*(?:&&|;|\|)\s*$", part):
            continue

        cmd_part = part.strip()
        if not cmd_part:
            continue

        # Check for allowed npm commands first
        is_allowed = False
        for allowed_cmd in Config.ALLOWED_NPM_COMMANDS:
            if allowed_cmd in cmd_part.lower():
                is_allowed = True
                break

        if is_allowed:
            continue

        # Detect npm/npx in this part
        if Config.NPM_PATTERN.search(cmd_part):
            pm = "npx" if "npx" in cmd_part.lower() else "npm"
            suggested = convert_to_bun(command, pm)
            return DetectionResult(
                detected=True,
                package_manager=pm,
                original_command=command,
                suggested_command=suggested,
            )

        # Detect pnpm in this part
        if Config.PNPM_PATTERN.search(cmd_part):
            suggested = convert_to_bun(command, "pnpm")
            return DetectionResult(
                detected=True,
                package_manager="pnpm",
                original_command=command,
                suggested_command=suggested,
            )

        # Detect yarn in this part
        if Config.YARN_PATTERN.search(cmd_part):
            suggested = convert_to_bun(command, "yarn")
            return DetectionResult(
                detected=True,
                package_manager="yarn",
                original_command=command,
                suggested_command=suggested,
            )

    return DetectionResult(
        detected=False,
        package_manager="",
        original_command=command,
        suggested_command="",
    )


def convert_to_bun(command: str, package_manager: str) -> str:
    """
    Convert npm/npx/pnpm/yarn command to Bun equivalent.

    Examples:
    - npm install → bun install
    - npm run dev → bun run dev (or bun dev)
    - npx create-react-app → bunx create-react-app
    - pnpm add lodash → bun add lodash
    - yarn build → bun run build (or bun build)
    """
    if package_manager == "npx":
        # npx → bunx
        return re.sub(r"\bnpx\b", "bunx", command, flags=re.IGNORECASE)

    if package_manager == "npm":
        # npm install → bun install
        # npm run X → bun run X (or bun X)
        # npm add/remove → bun add/remove
        result = re.sub(r"\bnpm\b", "bun", command, flags=re.IGNORECASE)

        # Optimize "bun run <script>" to "bun <script>" for common scripts
        result = re.sub(r"\bbun\s+run\s+(dev|build|start|test)\b", r"bun \1", result, flags=re.IGNORECASE)

        return result

    if package_manager == "pnpm":
        # pnpm → bun
        result = re.sub(r"\bpnpm\b", "bun", command, flags=re.IGNORECASE)

        # Optimize "bun run <script>"
        result = re.sub(r"\bbun\s+run\s+(dev|build|start|test)\b", r"bun \1", result, flags=re.IGNORECASE)

        return result

    if package_manager == "yarn":
        # yarn → bun run (for scripts) or bun (for other commands)
        # yarn add → bun add
        # yarn remove → bun remove
        # yarn dev → bun run dev (or bun dev)

        # First, handle yarn add/remove/install directly
        if re.search(r"\byarn\s+(add|remove|install)\b", command, re.IGNORECASE):
            return re.sub(r"\byarn\b", "bun", command, flags=re.IGNORECASE)

        # For script execution: yarn <script> → bun run <script>
        # But optimize common scripts to bun <script>
        result = re.sub(r"\byarn\s+(dev|build|start|test)\b", r"bun \1", command, flags=re.IGNORECASE)

        # If no optimization applied, do general replacement
        if result == command:
            result = re.sub(r"\byarn\b", "bun run", command, flags=re.IGNORECASE)

        return result

    return command


# Output handling
def handle_findings(result: DetectionResult) -> NoReturn:
    """Handle detection results and exit appropriately."""
    if not result["detected"]:
        sys.exit(0)

    message: str = build_error_message(result)
    print(message, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_BLOCK_TOOL)


def build_error_message(result: DetectionResult) -> str:
    """Build error message suggesting Bun alternative."""
    pm = result["package_manager"]
    original = result["original_command"]
    suggested = result["suggested_command"]

    return f"""🔒 BUN PROJECT DETECTED - {pm.upper()} BLOCKED

This is a Bun project (bun.lockb or packageManager field detected).
Use Bun instead of {pm} for better performance and compatibility.

❌ Blocked command:
{original}

✅ Use this instead:
{suggested}

💡 Quick reference:
  npm install → bun install
  npm run dev → bun dev
  npx <pkg>  → bunx <pkg>
  pnpm add X → bun add X
  yarn build → bun build

Note: Global npm commands (publish, login, etc.) are still allowed.
"""


def handle_hook_error() -> NoReturn:
    """Handle errors in hook execution."""
    # Silently allow on error (fail-open for hook errors)
    sys.exit(0)


if __name__ == "__main__":
    main()
