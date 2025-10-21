#!/usr/bin/env python3
"""
Python opinionated code checkers entrypoint that runs fix_* first, then check_* scripts.

Usage:
    echo '{"tool_name": "Write", "tool_input": {...}}' | python python_1_opinionated.py
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

        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(stdin_data.encode()), timeout=30.0)

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

    checkers_dir = Path(__file__).parent / "python_opinionated"

    # Find fix_* and check_* files separately
    fix_files = sorted(checkers_dir.glob("fix_*.py"))
    check_files = sorted(checkers_dir.glob("check_*.py"))

    claude_needs_to_know = False

    # Run fix_* files first (in parallel with each other)
    if fix_files:
        fix_tasks = [execute_checker_async(str(fix_path), stdin_data, current_cwd) for fix_path in fix_files]
        fix_results: list[tuple[int, str, str] | BaseException] = await asyncio.gather(
            *fix_tasks, return_exceptions=True
        )

        for fix_path, result in zip(fix_files, fix_results, strict=False):
            if isinstance(result, BaseException):
                continue

            returncode, _stdout, stderr = result
            if returncode == 2 and stderr:
                claude_needs_to_know = True
                print(stderr, file=sys.stderr, end="")

    # Then run check_* files (in parallel with each other)
    if check_files:
        check_tasks = [execute_checker_async(str(check_path), stdin_data, current_cwd) for check_path in check_files]
        check_results: list[tuple[int, str, str] | BaseException] = await asyncio.gather(
            *check_tasks, return_exceptions=True
        )

        for check_path, result in zip(check_files, check_results, strict=False):
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
