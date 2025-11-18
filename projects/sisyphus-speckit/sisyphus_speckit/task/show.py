from __future__ import annotations

import typer
from rich.panel import Panel
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _format_task_display, _load_current_plan, _run_async, console


def show_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    rich: bool = typer.Option(
        False,
        "--rich",
        help="Rich formatting (legacy option, always enabled)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    async def _show() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        task = task_manager.find_todo_by_id(task_id)
        if task is None:
            console.print(f"[red]작업 ID를 찾을 수 없습니다: {task_id}[/red]")
            raise typer.Exit(1)

        display = _format_task_display(task)
        console.print(Panel(display, title=f"작업 {task_id}", border_style="cyan"))

    _run_async(_show())
