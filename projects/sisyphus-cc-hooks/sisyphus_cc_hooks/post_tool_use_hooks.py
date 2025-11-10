from __future__ import annotations

from collections.abc import Callable

from .post_tool_use_executor_verification import main as verification_main
from .post_tool_use_plan_lint import main as plan_lint_main

POST_TOOL_USE_HOOKS: list[Callable[[], int]] = [
    verification_main,
    plan_lint_main,
]
