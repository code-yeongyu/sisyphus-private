"""Plan status display command."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, TextColumn
from rich.progress import Progress as RichProgress
from sisyphus_core.core.plans.loader import load_plan
from sisyphus_core.core.plans.models import Todo
from sisyphus_core.core.task_manager import TaskManager
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import (
    _display_verification_status_table,
    _load_current_plan,
    _run_async,
)

console = Console()


def _count_all_todos(todos: list[Todo]) -> int:
    count = 0
    for todo in todos:
        count += 1
        if todo.children:
            count += _count_all_todos(todo.children)
    return count


def _count_completed_todos(todos: list[Todo]) -> int:
    count = 0
    for todo in todos:
        if todo.computed_status.value == "completed":
            count += 1
        if todo.children:
            count += _count_completed_todos(todo.children)
    return count


def status(
    path: Path | None = typer.Option(None, "--path", "-p", help="Path to specific plan file"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display plan status including progress bar and verification summary.

    If --path is provided, displays status for that specific plan.
    Otherwise, displays status for the current active plan.
    """

    async def _status() -> None:
        working_dir = resolve_cwd(cwd)

        if path:
            try:
                plan_path = Path(path)
                if not plan_path.is_absolute():
                    plan_path = working_dir / plan_path
                plan_doc = await load_plan(plan_path)
            except Exception as e:
                console.print(f"[red]Error loading plan:[/red] {e}")
                raise typer.Exit(code=1)

            if not plan_doc.work_plans:
                console.print("[red]No work_plans found in the plan file.[/red]")
                raise typer.Exit(code=1)

            work_plan = plan_doc.work_plans[0]
            task_manager = TaskManager(plan_doc, work_plan.id)
        else:
            plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        total_todos = _count_all_todos(work_plan.todos)
        completed_todos = _count_completed_todos(work_plan.todos)
        progress_pct = (completed_todos / total_todos * 100) if total_todos > 0 else 0

        console.print(f"\n[bold cyan]Plan:[/bold cyan] {work_plan.name}")
        console.print(f"[bold cyan]ID:[/bold cyan] {work_plan.id}")

        console.print(f"[bold cyan]Total Tasks:[/bold cyan] {total_todos}")
        console.print(f"[bold cyan]Completed:[/bold cyan] {completed_todos}")
        console.print(f"[bold cyan]Progress:[/bold cyan] {progress_pct:.1f}%")

        fully_done = work_plan.execution.fully_done_at is not None
        fully_done_str = "[green]Yes (fully_done_at is set)[/green]" if fully_done else "[yellow]No[/yellow]"
        console.print(f"[bold cyan]Fully Done:[/bold cyan] {fully_done_str}")

        with RichProgress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task(f"Plan Progress: {work_plan.name}", total=total_todos)
            progress.update(task, completed=completed_todos)

        console.print()
        _display_verification_status_table(work_plan, task_manager, show_current_task=True)

    _run_async(_status())
