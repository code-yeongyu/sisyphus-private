from __future__ import annotations

import io
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import NotRequired, TypedDict, cast

import anyio  # type: ignore[import-not-found]

from ._compat_anyio import run_sync
from .pre_tool_use_plan_delegation import main as plan_delegation_main


class ToolInputData(TypedDict):
    tool_name: NotRequired[str]
    tool_input: NotRequired[dict[str, str]]
    cwd: NotRequired[str]


@dataclass
class HookCommand:
    type: str
    command: Callable[[], int]
    asyncable: bool = False


@dataclass
class HookMatcher:
    matcher: str
    hooks: list[HookCommand]


PRE_TOOL_USE_CONFIG: list[HookMatcher] = [
    HookMatcher(
        matcher="Write|Edit|MultiEdit|NotebookEdit",
        hooks=[
            HookCommand(
                type="function",
                command=plan_delegation_main,
                asyncable=True,
            ),
        ],
    ),
]

TOOL_PATTERN = re.compile(r"^(.+)$")


def match_tool(tool_name: str, matcher: str) -> bool:
    pattern = re.compile(f"^({matcher})$")
    return bool(pattern.match(tool_name))


async def execute_hook_in_thread(func: Callable[[], int], stdin_data: str) -> int:
    def _run() -> int:
        sys.stdin = io.StringIO(stdin_data)
        return func()

    try:
        result: int = await run_sync(_run)
        return result
    except Exception as e:
        print(f"Hook execution failed: {e}", file=sys.stderr)
        return 1


async def _main() -> int:
    tool_name: str | None = None
    if len(sys.argv) > 1 and sys.argv[1] == "--tool" and len(sys.argv) > 2:
        tool_name = sys.argv[2]

    stdin_data = sys.stdin.read()

    if stdin_data:
        try:
            input_json = cast(ToolInputData, json.loads(stdin_data))
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

    valid_hooks = [hook for hook in matching_hooks if hook.type == "function"]

    if not valid_hooks:
        return 0

    async_hooks = [hook for hook in valid_hooks if hook.asyncable]
    sync_hooks = [hook for hook in valid_hooks if not hook.asyncable]
    hooks_want_to_block = False
    results: list[int] = []

    if async_hooks:

        async def run_and_collect(func: Callable[[], int]) -> None:
            result = await execute_hook_in_thread(func, stdin_data)
            results.append(result)

        async with anyio.create_task_group() as tg:
            for hook in async_hooks:
                tg.start_soon(run_and_collect, hook.command)

        for exit_code in results:
            if exit_code == 2:
                hooks_want_to_block = True

    for hook in sync_hooks:
        exit_code = await execute_hook_in_thread(hook.command, stdin_data)
        if exit_code == 2:
            hooks_want_to_block = True

    return 2 if hooks_want_to_block else 0


def main() -> int:
    return anyio.run(_main)


if __name__ == "__main__":
    sys.exit(main())
