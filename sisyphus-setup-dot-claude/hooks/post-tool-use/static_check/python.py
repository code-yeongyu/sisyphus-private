#!/usr/bin/env python3
"""
Python static checkers entrypoint that runs all python_* scripts in parallel.

Usage:
    echo '{"tool_name": "Write", "tool_input": {...}}' | python python.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path


async def execute_checker_async(checker_path: str, stdin_data: str, cwd: str) -> tuple[int, str, str]:
    try:
        process = await asyncio.create_subprocess_shell(
            f"uv run {checker_path}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(stdin_data.encode()), timeout=60.0)

        return (
            process.returncode or 0,
            stdout_bytes.decode(errors="replace"),
            stderr_bytes.decode(errors="replace"),
        )
    except TimeoutError:
        return 1, "", f"Checker {checker_path} execution timed out"
    except Exception as e:
        return 1, "", f"Checker {checker_path} execution failed: {e}"


async def _main() -> int:
    stdin_data = sys.stdin.read()

    # Extract actual Claude Code cwd from stdin JSON
    current_cwd = os.getcwd()
    if stdin_data:
        try:
            input_json = json.loads(stdin_data)
            current_cwd = input_json.get("cwd", os.getcwd())
        except json.JSONDecodeError:
            pass

    # Find all python_* files in the same directory
    checkers_dir = Path(__file__).parent
    checker_files = sorted(checkers_dir.glob("python_*.py"))

    if not checker_files:
        return 0

    # Run all checkers in parallel
    tasks = [execute_checker_async(str(checker_path), stdin_data, current_cwd) for checker_path in checker_files]
    results: list[tuple[int, str, str] | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)

    claude_needs_to_know = False

    for checker_path, result in zip(checker_files, results, strict=False):
        if isinstance(result, BaseException):
            continue

        returncode, _stdout, stderr = result
        if returncode == 2 and stderr:
            claude_needs_to_know = True
            print(stderr, file=sys.stderr, end="")

    return 2 if claude_needs_to_know else 0


def main() -> int:
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
