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


class StaticChecker:
    """Execute language-specific static checkers when writing/editing code files."""

    STATIC_CHECK_DIR = Path.home() / ".claude" / "hooks" / "post-tool-use" / "static_check"

    # Extension to language mapping
    EXTENSION_MAP = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".swift": "swift",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".tf": "terraform",
        ".tfvars": "terraform",
    }

    def __init__(self, cwd: str, transcript_path: str) -> None:
        self.cwd = Path(cwd)
        self.transcript_path = Path(transcript_path)

    def _get_language_from_extension(self, extension: str) -> str | None:
        if not extension or not extension.startswith("."):
            return None
        # Try to get from map first
        language = self.EXTENSION_MAP.get(extension)
        if language:
            return language
        # Fallback: use extension itself as language name (without the dot)
        return extension[1:]

    def _get_checker_path(self, language: str) -> Path | None:
        checker_path = self.STATIC_CHECK_DIR / f"{language}.py"
        return checker_path if checker_path.exists() else None

    def _execute_checker(self, checker_path: Path, stdin_data: str) -> tuple[int, str, str]:
        try:
            result = subprocess.run(
                ["uv", "run", str(checker_path)],
                check=False,
                input=stdin_data.encode(),
                capture_output=True,
                timeout=30.0,
                cwd=str(self.cwd),
            )
            return (
                result.returncode,
                result.stdout.decode(errors="replace"),
                result.stderr.decode(errors="replace"),
            )
        except subprocess.TimeoutExpired:
            return 1, "", "Static checker execution timed out"
        except Exception as e:
            return 1, "", f"Static checker execution failed: {e}"

    def check(self, file_path: str, stdin_data: str) -> tuple[int, str, str]:
        path = Path(file_path)
        extension = path.suffix

        language = self._get_language_from_extension(extension)
        if not language:
            return 0, "", ""

        checker_path = self._get_checker_path(language)
        if not checker_path:
            return 0, "", ""

        return self._execute_checker(checker_path, stdin_data)


def main() -> None:
    """Main entry point for the hook."""
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

    if tool_name not in ("Read", "Write", "Edit", "MultiEdit"):
        print(f"[{hook_filename}] Skipping: Tool {tool_name} not relevant")
        sys.exit(0)

    tool_input = data["tool_input"]
    file_path = tool_input.get("file_path", "")

    if not file_path:
        print(f"[{hook_filename}] Skipping: No file path provided")
        sys.exit(0)

    if Path(file_path).resolve() == Path(__file__).resolve():
        print(f"[{hook_filename}] Skipping: Self-reference detected")
        sys.exit(0)

    cwd = data["cwd"]
    transcript_path = data["transcript_path"]

    checker = StaticChecker(cwd, transcript_path)
    returncode, stdout, stderr = checker.check(file_path, input_raw)

    if returncode == 2:
        # Checker found issues that Claude needs to know about
        if stdout:
            print(stdout, file=sys.stdout)
        if stderr:
            print(stderr, file=sys.stderr)
        sys.exit(2)
    elif returncode != 0:
        # Checker had an error but not critical
        if stderr:
            print(stderr, file=sys.stderr)
        sys.exit(0)

    print(f"[{hook_filename}] Success: No static check issues")
    sys.exit(0)


if __name__ == "__main__":
    main()
