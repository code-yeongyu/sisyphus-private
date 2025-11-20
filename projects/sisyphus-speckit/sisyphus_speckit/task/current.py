from __future__ import annotations

import typer
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _load_current_plan, _run_async, console
from sisyphus_speckit.task.show import _show_task_impl


def show_current(
    _rich: bool = typer.Option(
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

        await _show_task_impl(current_task, work_plan, working_dir)

        console.print("\n[dim]💡 Tip: 검증 스펙 상세는 'sisyphus-speckit task status' 실행[/dim]")

    _run_async(_current())
