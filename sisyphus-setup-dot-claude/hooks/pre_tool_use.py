#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass


@dataclass
class HookCommand:
    type: str
    command: str
    asyncable: bool = False


@dataclass
class HookMatcher:
    matcher: str
    hooks: list[HookCommand]


PRE_TOOL_USE_CONFIG: list[HookMatcher] = [
    HookMatcher(
        matcher="Bash",
        hooks=[
            HookCommand(
                type="command",
                command="uv run ~/.claude/hooks/pre-tool-use/block_npm_in_bun_projects.py",
                asyncable=True,
            ),
            HookCommand(
                type="command",
                command="uv run ~/.claude/hooks/pre-tool-use/block_poetry_pip_in_uv_projects.py",
                asyncable=True,
            ),
            HookCommand(
                type="command",
                command="uv run ~/.claude/hooks/pre-tool-use/block_git_push_to_protected_branches.py",
                asyncable=True,
            ),
        ],
    ),
    HookMatcher(
        matcher="Write|Edit|MultiEdit",
        hooks=[
            HookCommand(
                type="command",
                command="uv run ~/.claude/hooks/pre-tool-use/block_asyncio_when_anyio_exists.py",
                asyncable=True,
            ),
            HookCommand(
                type="command",
                command="uv run ~/.claude/hooks/pre-tool-use/block_json_when_orjson_exists.py",
                asyncable=True,
            ),
        ],
    ),
    HookMatcher(
        matcher="Task",
        hooks=[
            HookCommand(
                type="command",
                command="uv run ~/.claude/hooks/pre-tool-use/block_executor_without_execute_command.py",
                asyncable=True,
            ),
        ],
    ),
]


def match_tool(tool_name: str, matcher: str) -> bool:
    pattern = f"^({matcher})$"
    return bool(re.match(pattern, tool_name))


def is_self_hook(command: str) -> bool:
    return "pre_tool_use.py" in command


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
    tool_name: str | None = None
    if len(sys.argv) > 1 and sys.argv[1] == "--tool" and len(sys.argv) > 2:
        tool_name = sys.argv[2]

    stdin_data = sys.stdin.read()

    current_cwd = os.getcwd()
    if stdin_data:
        try:
            input_json = json.loads(stdin_data)
            current_cwd = input_json.get("working_directory", os.getcwd())
            if not tool_name:
                tool_name = input_json.get("tool_name")
        except json.JSONDecodeError:
            pass

    if not tool_name:
        print("Error: tool_name not provided", file=sys.stderr)
        return 1

    matching_hooks: list[HookCommand] = []
    for config in PRE_TOOL_USE_CONFIG:
        if match_tool(tool_name, config.matcher):
            matching_hooks.extend(config.hooks)

    if not matching_hooks:
        return 0

    valid_hooks = [
        hook for hook in matching_hooks if hook.type == "command" and hook.command and not is_self_hook(hook.command)
    ]

    if not valid_hooks:
        return 0

    async_hooks = [hook for hook in valid_hooks if hook.asyncable]
    sync_hooks = [hook for hook in valid_hooks if not hook.asyncable]
    hooks_want_to_block = False

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
                hooks_want_to_block = True
                print(stderr, file=sys.stderr, end="")

    for hook in sync_hooks:
        returncode, _stdout, stderr = await execute_hook_async(hook.command, stdin_data, current_cwd)

        if returncode == 2 and stderr:
            hooks_want_to_block = True
            print(f"Hook Executed: {hook.command}", file=sys.stderr)
            print(stderr, file=sys.stderr, end="")

    exit_code = 0
    if hooks_want_to_block:
        exit_code = 2

    return exit_code


def main() -> int:
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
