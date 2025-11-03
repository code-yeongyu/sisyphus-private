#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false
"""
Stop hook that blocks session termination when static check failures exist.

This hook parses the transcript to find all modified files (Write/Edit operations),
runs language-specific static checkers, and blocks stop if any issues are found.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, NoReturn, TypedDict


class StopInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str


class StopCheckInput(TypedDict):
    file_path: str
    cwd: str


class CheckResult(TypedDict):
    file_path: str
    has_errors: bool
    checker_name: str
    error_output: str


class Config:
    EXIT_CODE_ALLOW: int = 0
    EXIT_CODE_BLOCK: int = 2
    CHECKER_TIMEOUT_SECONDS: float = 60.0
    STATIC_CHECK_DIR: Path = Path(__file__).parent / "static_check"

    EXTENSION_MAP: dict[str, str] = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
    }


def main() -> None:
    log_path = Path.home() / ".claude" / "hook_debug.log"
    try:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write("\n=== Static Check Stop Hook ===\n")
            input_data = sys.stdin.read()
            log_file.write(f"Input: {input_data}\n")

        execute_hook_pipeline(input_data)
    except Exception as exception:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"Exception: {exception}\n")
        sys.exit(Config.EXIT_CODE_ALLOW)


def execute_hook_pipeline(input_data: str) -> NoReturn:
    data = parse_input(input_data)

    session_id = data.get("session_id", "")
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", "")

    if not session_id or not transcript_path:
        sys.exit(Config.EXIT_CODE_ALLOW)

    modified_files = extract_modified_files(Path(transcript_path))

    if not modified_files:
        sys.exit(Config.EXIT_CODE_ALLOW)

    results = check_all_files(modified_files, cwd)
    handle_results(results)


def parse_input(input_raw: str) -> StopInput:
    if not input_raw.strip():
        sys.exit(Config.EXIT_CODE_ALLOW)

    try:
        data: StopInput = json.loads(input_raw)
        return data
    except json.JSONDecodeError:
        sys.exit(Config.EXIT_CODE_ALLOW)


def extract_modified_files(transcript_path: Path) -> set[str]:
    modified_files: set[str] = set()

    if not transcript_path.exists():
        return modified_files

    try:
        with transcript_path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                try:
                    event = json.loads(stripped_line)
                    file_path = extract_file_path_from_event(event)
                    if file_path:
                        modified_files.add(file_path)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return modified_files


def extract_file_path_from_event(event: dict[str, Any]) -> str | None:
    if event.get("type") == "tool_use":
        tool_name = event.get("name", "")
        if tool_name in ("Write", "Edit"):
            tool_input = event.get("input", {})
            return tool_input.get("file_path")

    if event.get("type") == "message":
        content = event.get("content", [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name", "")
                    if tool_name in ("Write", "Edit"):
                        tool_input = item.get("input", {})
                        file_path = tool_input.get("file_path")
                        if file_path:
                            return file_path

    return None


def check_all_files(files: set[str], cwd: str) -> list[CheckResult]:
    results: list[CheckResult] = []

    for file_path in sorted(files):
        path = Path(file_path)

        if not path.exists():
            continue

        extension = path.suffix
        language = Config.EXTENSION_MAP.get(extension)

        if not language:
            continue

        checker_path = Config.STATIC_CHECK_DIR / f"{language}.py"
        if not checker_path.exists():
            continue

        result = run_checker(checker_path, file_path, cwd)
        if result["has_errors"]:
            results.append(result)

    return results


def run_checker(checker_path: Path, file_path: str, cwd: str) -> CheckResult:
    stdin_data: StopCheckInput = {
        "file_path": file_path,
        "cwd": cwd,
    }

    try:
        result = subprocess.run(
            ["uv", "run", str(checker_path)],
            check=False,
            input=json.dumps(stdin_data).encode(),
            capture_output=True,
            timeout=Config.CHECKER_TIMEOUT_SECONDS,
            cwd=cwd,
        )

        has_errors = result.returncode == Config.EXIT_CODE_BLOCK
        error_output = result.stderr.decode(errors="replace") if has_errors else ""

        return CheckResult(
            file_path=file_path,
            has_errors=has_errors,
            checker_name=checker_path.stem,
            error_output=error_output,
        )

    except subprocess.TimeoutExpired:
        return CheckResult(
            file_path=file_path,
            has_errors=True,
            checker_name=checker_path.stem,
            error_output=f"Checker execution timed out after {Config.CHECKER_TIMEOUT_SECONDS}s",
        )
    except Exception as exception:
        return CheckResult(
            file_path=file_path,
            has_errors=True,
            checker_name=checker_path.stem,
            error_output=f"Checker execution failed: {exception}",
        )


def handle_results(results: list[CheckResult]) -> NoReturn:
    if not results:
        sys.exit(Config.EXIT_CODE_ALLOW)

    message_parts = [
        "",
        "=" * 80,
        "STATIC CHECK FAILURES - CANNOT CLOSE SESSION",
        "=" * 80,
        "",
        f"Found issues in {len(results)} file(s).",
        "You must fix all errors before closing this session.",
        "",
    ]

    for result in results:
        message_parts.append(f"File: {result['file_path']}")
        message_parts.append("-" * 80)
        if result["error_output"]:
            message_parts.append(result["error_output"])
        message_parts.append("")

    message_parts.extend(
        [
            "=" * 80,
            "FIX ALL ERRORS ABOVE BEFORE ATTEMPTING TO CLOSE THE SESSION.",
            "=" * 80,
        ]
    )

    error_message = "\n".join(message_parts)

    response = {
        "decision": "block",
        "reason": error_message,
    }

    print(json.dumps(response), file=sys.stdout)
    sys.exit(Config.EXIT_CODE_BLOCK)


if __name__ == "__main__":
    main()
