#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import asyncio
import json
import os
import sys
from dataclasses import dataclass


@dataclass
class HookCommand:
    type: str
    command: str
    asyncable: bool = False


PRE_COMPACT_HOOKS: list[HookCommand] = [
    HookCommand(
        type="command",
        command="~/.claude/hooks/pre-compact/backup_transcript.py",
        asyncable=False,
    ),
]


def is_self_hook(command: str) -> bool:
    return "pre_compact.py" in command


async def execute_hook_async(command: str, stdin_data: str, cwd: str) -> tuple[int, str, str]:
    try:
        process = await asyncio.create_subprocess_shell(
            command,
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
        return 1, "", "Hook execution timed out"
    except Exception as e:
        return 1, "", f"Hook execution failed: {e}"


async def _main() -> int:
    stdin_data = sys.stdin.read()

    current_cwd = os.getcwd()
    if stdin_data:
        try:
            input_json = json.loads(stdin_data)
            current_cwd = input_json.get("cwd", os.getcwd())
        except json.JSONDecodeError:
            pass

    valid_hooks = [
        hook
        for hook in PRE_COMPACT_HOOKS
        if hook.type == "command" and hook.command and not is_self_hook(hook.command)
    ]

    if not valid_hooks:
        return 0

    async_hooks = [hook for hook in valid_hooks if hook.asyncable]
    sync_hooks = [hook for hook in valid_hooks if not hook.asyncable]
    claude_needs_to_know = False

    if async_hooks:
        tasks = [execute_hook_async(hook.command, stdin_data, current_cwd) for hook in async_hooks]
        results: list[tuple[int, str, str] | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)

        for hook, result in zip(async_hooks, results, strict=False):
            if isinstance(result, BaseException):
                print(
                    f"Error executing hook: {hook.command}. WARN TO USER THIS HAS FAILED. {result=}",
                    file=sys.stderr,
                )
                continue

            returncode, _stdout, stderr = result
            if returncode == 2 and stderr:
                claude_needs_to_know = True
                print(stderr, file=sys.stderr, end="")

    for hook in sync_hooks:
        returncode, _stdout, stderr = await execute_hook_async(hook.command, stdin_data, current_cwd)

        if returncode == 2 and stderr:
            claude_needs_to_know = True
            print(f"Hook Executed: {hook.command}", file=sys.stderr)
            print(stderr, file=sys.stderr, end="")

    exit_code = 0
    if claude_needs_to_know:
        exit_code = 2

    return exit_code


def main() -> int:
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
