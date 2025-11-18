"""Plan status display command."""

from __future__ import annotations

import typer
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import (
    _display_verification_status_table,
    _load_current_plan,
    _run_async,
)


def status(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display verification status for all tasks."""

    async def _status() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        _display_verification_status_table(work_plan, task_manager, show_current_task=True)

    _run_async(_status())
