from __future__ import annotations

import typer
from rich.panel import Panel
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _format_task_display, _load_current_plan, _run_async, console


def show_previous(
    _rich: bool = typer.Option(
        False,
        "--rich",
        help="Rich formatting (legacy option, always enabled)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    async def _previous() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        current_task = task_manager.get_current_task()
        if current_task is None:
            console.print("[yellow]작업이 시작되지 않았습니다.[/yellow]")
            return

        previous_task = task_manager.get_previous_task()
        if previous_task is None:
            console.print("[yellow]첫 작업입니다.[/yellow]")
            return

        display = _format_task_display(previous_task)
        console.print(Panel(display, title="이전 작업", border_style="blue"))

    _run_async(_previous())
