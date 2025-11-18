from __future__ import annotations

import typer
from rich.panel import Panel
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _format_task_display, _load_current_plan, _run_async, console


def show_current(
    rich: bool = typer.Option(
        False,
        "--rich",
        help="Rich formatting (legacy option, always enabled)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    async def _current() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        current_task = task_manager.get_current_task()
        if current_task is None:
            console.print("[yellow]작업이 시작되지 않았습니다.[/yellow]")
            console.print("다음 명령으로 작업을 시작하세요: [cyan]sisyphus-speckit task continue[/cyan]")
            return

        display = _format_task_display(current_task)
        console.print(Panel(display, title="현재 작업", border_style="green"))

    _run_async(_current())
