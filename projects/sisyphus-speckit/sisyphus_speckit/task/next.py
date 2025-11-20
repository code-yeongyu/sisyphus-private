from __future__ import annotations

import typer
from rich.panel import Panel
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _format_task_display, _load_current_plan, _run_async, console


def show_next(
    _rich: bool = typer.Option(
        False,
        "--rich",
        help="Rich formatting (legacy option, always enabled)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    async def _next() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        next_task = task_manager.get_next_task()
        if next_task is None:
            console.print("[green]모든 작업이 완료되었습니다! 🎉[/green]")
            return

        display = _format_task_display(next_task)
        console.print(Panel(display, title="다음 작업", border_style="yellow"))

    _run_async(_next())
