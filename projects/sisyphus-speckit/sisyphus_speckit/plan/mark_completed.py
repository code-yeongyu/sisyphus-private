from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, cast

import anyio
import typer
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.status.manager import StatusManager
from sisyphus_core.core.task_manager import TaskManager
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import (
    _display_remaining_verifications,
    _format_task_display,
    console,
)


def mark_completed_command(
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory")] = None,
) -> None:
    """Mark work plan as completed when all todos are done.

    This command checks if all todos in the plan have been completed.
    If all todos are completed, it marks the plan as completed.
    If any todos are incomplete, it shows guidance and the current task.
    """

    async def _mark_completed() -> None:
        working_dir = resolve_cwd(cwd)
        status_path = working_dir / ".sisyphus" / "status.json"

        status_manager = StatusManager(status_path)
        status = await status_manager.get()

        if status.current_plan is None:
            console.print("[red]현재 활성화된 작업 계획이 없습니다.[/red]")
            raise typer.Exit(1)

        plan_path = working_dir / status.current_plan.plan_path
        plan_doc = await load_plan(plan_path)

        if not plan_doc.work_plans:
            console.print("[red]작업 계획에 work_plans가 없습니다.[/red]")
            raise typer.Exit(1)

        work_plan = plan_doc.work_plans[0]
        task_manager = TaskManager(plan_doc, work_plan.id)

        # Check all todos for completion
        all_todos_completed = True
        incomplete_todos = []

        for todo in work_plan.todos:
            completion_report = task_manager.check_task_completion(todo.id)
            if not completion_report.can_complete:
                all_todos_completed = False
                incomplete_todos.append(todo)

        if all_todos_completed:
            # Mark as completed
            work_plan.execution.completed = True
            work_plan.execution.completed_at = datetime.now(UTC).isoformat()
            await save_plan(plan_path, plan_doc)
            console.print("[green]✓ 모든 작업이 완료되었습니다![/green]")
            console.print(f"[cyan]완료 시각:[/cyan] {work_plan.execution.completed_at}")
        else:
            # Show incomplete message and current task
            console.print("[yellow]⚠ 모든 작업이 완료되지 않았습니다.[/yellow]")
            incomplete_count = len(cast(list[Any], incomplete_todos))
            console.print(f"[yellow]미완료 작업:[/yellow] {incomplete_count}개")
            console.print()
            console.print("[cyan]다음 명령으로 계속 진행하세요:[/cyan]")
            console.print("  [bold]sisyphus-speckit task continue[/bold]")
            console.print()

            # Show current task
            current_task = task_manager.get_current_task()
            if current_task is not None:
                console.print("[bold cyan]현재 작업:[/bold cyan]")
                display = _format_task_display(current_task, show_children=False, show_verification=True)
                console.print(display)
                _display_remaining_verifications(task_manager)

            raise typer.Exit(1)

    anyio.run(_mark_completed)
