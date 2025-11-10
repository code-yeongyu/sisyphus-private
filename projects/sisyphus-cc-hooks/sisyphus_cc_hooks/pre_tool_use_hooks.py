from __future__ import annotations

from collections.abc import Callable

from .pre_tool_use_plan_delegation import main as plan_delegation_main

PRE_TOOL_USE_HOOKS: list[Callable[[], int]] = [
    plan_delegation_main,
]
