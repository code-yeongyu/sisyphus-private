"""Plan overview display command."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, TextColumn
from rich.progress import Progress as RichProgress
from rich.table import Table
from sisyphus_core.core.plans.loader import load_plan
from sisyphus_core.core.plans.models import Todo
from sisyphus_core.core.task_manager import TaskManager
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _load_current_plan, _run_async

console = Console()


def _count_all_todos(todos: list[Todo]) -> int:
    """Count all todos recursively."""
    count = 0
    for todo in todos:
        count += 1
        if todo.children:
            count += _count_all_todos(todo.children)
    return count


def _count_completed_todos(todos: list[Todo]) -> int:
    """Count completed todos recursively."""
    count = 0
    for todo in todos:
        if todo.computed_status.value == "completed":
            count += 1
        if todo.children:
            count += _count_completed_todos(todo.children)
    return count


def plan_overview(
    path: Path | None = typer.Option(None, "--path", "-p", help="Path to specific plan file"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display comprehensive plan overview including all metadata.

    If --path is provided, displays overview for that specific plan.
    Otherwise, displays overview for the current active plan.
    """

    async def _overview() -> None:
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

        # Calculate progress
        total_todos = _count_all_todos(work_plan.todos)
        completed_todos = _count_completed_todos(work_plan.todos)
        progress_pct = (completed_todos / total_todos * 100) if total_todos > 0 else 0

        # 1. Plan Header
        console.print(Panel(f"[bold cyan]{work_plan.name}[/bold cyan]", title="Plan Overview"))

        # 2. Plan Metadata
        console.print("\n[bold]Plan Information:[/bold]")
        console.print(f"  ID: {work_plan.id}")
        console.print(f"  Total Tasks: {total_todos}")
        console.print(f"  Completed: {completed_todos}/{total_todos}")
        console.print(f"  Progress: {progress_pct:.1f}%")

        fully_done = work_plan.execution.fully_done_at is not None
        fully_done_str = "[green]Yes (fully_done_at is set)[/green]" if fully_done else "[yellow]No[/yellow]"
        console.print(f"  Fully Done: {fully_done_str}")

        # 3. Progress Bar
        with RichProgress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task(f"Plan Progress: {work_plan.name}", total=total_todos)
            progress.update(task, completed=completed_todos)

        # 4. User Request
        console.print("\n[bold]User Request:[/bold]")
        console.print(work_plan.user_request.original)

        if work_plan.user_request.additional:
            console.print("\n[bold]Additional Requirements:[/bold]")
            for item in work_plan.user_request.additional:
                console.print(f"  • {item}")

        # 5. Objectives
        console.print("\n[bold]Objectives:[/bold]")
        console.print("\n[cyan]Core Objective:[/cyan]")
        console.print(f"  {work_plan.objectives.core}")

        if work_plan.objectives.detailed:
            console.print("\n[cyan]Detailed Objectives:[/cyan]")
            for obj in work_plan.objectives.detailed:
                console.print(f"  • Goal: {obj.goal}")
                console.print(f"    Measurable: {obj.measurable}")

        # 6. Background
        console.print("\n[bold]Background:[/bold]")
        bg = work_plan.background
        console.print("\n[cyan]Current Situation:[/cyan]")
        console.print(f"  {bg.current_situation}")
        console.print("\n[cyan]Reason for Change:[/cyan]")
        console.print(f"  {bg.reason_for_change}")
        console.print("\n[cyan]Changes to Make:[/cyan]")
        console.print(f"  {bg.changes_to_make}")

        # 7. Required Background
        if work_plan.required_background:
            console.print("\n[bold]Required Background:[/bold]")
            if work_plan.required_background.description:
                console.print("\n[cyan]Description:[/cyan]")
                console.print(f"  {work_plan.required_background.description}")

            if work_plan.required_background.references:
                console.print("\n[cyan]References:[/cyan]")
                for ref in work_plan.required_background.references:
                    console.print(f"  • {ref.ref_id}: {ref.uri}")

        # 8. Workflow
        if work_plan.workflow:
            console.print("\n[bold]Workflow:[/bold]")
            if work_plan.workflow.dependency_diagram:
                console.print("\n[cyan]Dependency Diagram:[/cyan]")
                console.print(work_plan.workflow.dependency_diagram)

            if work_plan.workflow.critical_path:
                console.print("\n[cyan]Critical Path:[/cyan]")
                for task_id in work_plan.workflow.critical_path:
                    console.print(f"  • Task {task_id}")

        # 9. Success Vision
        if work_plan.success_vision:
            console.print("\n[bold]Success Vision:[/bold]")

            if work_plan.success_vision.user_perspective:
                console.print("\n[cyan]User Perspective:[/cyan]")
                for scenario in work_plan.success_vision.user_perspective:
                    console.print(f"  • Scenario: {scenario.scenario}")
                    console.print(f"    Experience: {scenario.experience}")

            if work_plan.success_vision.business_perspective:
                console.print("\n[cyan]Business Perspective:[/cyan]")
                for perspective in work_plan.success_vision.business_perspective:
                    console.print(f"  • Metric: {perspective.metric}")
                    console.print(f"    Target: {perspective.target}")

            if work_plan.success_vision.technical_criteria:
                console.print("\n[cyan]Technical Criteria:[/cyan]")
                for criteria in work_plan.success_vision.technical_criteria:
                    console.print(f"  • Category: {criteria.category}")
                    console.print(f"    Criteria: {criteria.criteria}")
                    if criteria.command:
                        console.print(f"    Command: {criteria.command}")
                    if criteria.expected:
                        console.print(f"    Expected: {criteria.expected}")

        # 10. Final Verification
        if work_plan.final_verification:
            console.print("\n[bold]Final Verification:[/bold]")
            verification_table = Table(title="Verification Specs")
            verification_table.add_column("ID", style="cyan")
            verification_table.add_column("Title", style="magenta")
            verification_table.add_column("Category", style="yellow")
            verification_table.add_column("Verified", style="green")

            for verification in work_plan.final_verification:
                verified_status = "[green]✓ Yes[/green]" if verification.verified else "[red]✗ No[/red]"
                verification_table.add_row(verification.id, verification.title, verification.category, verified_status)

            console.print(verification_table)

            console.print("\n[cyan]Verification Details:[/cyan]")
            for verification in work_plan.final_verification:
                console.print(f"\n  [{verification.id}] {verification.title}")
                console.print(f"    Description: {verification.description}")
                if verification.bash:
                    console.print("    Bash Commands:")
                    for bash_cmd in verification.bash:
                        console.print(f"      • execute: {bash_cmd.execute}")
                        console.print(f"        expected_exit_code: {bash_cmd.expected_exit_code}")

        # 11. Acceptance Criteria
        if hasattr(work_plan, "acceptance_criteria") and work_plan.acceptance_criteria:
            console.print("\n[bold]Acceptance Criteria:[/bold]")
            acceptance_table = Table(title="Acceptance Criteria")
            acceptance_table.add_column("ID", style="cyan")
            acceptance_table.add_column("Title", style="magenta")
            acceptance_table.add_column("Category", style="yellow")

            for criterion in work_plan.acceptance_criteria:
                acceptance_table.add_row(criterion.id, criterion.title, criterion.category)

            console.print(acceptance_table)

            console.print("\n[cyan]Criteria Details:[/cyan]")
            for criterion in work_plan.acceptance_criteria:
                console.print(f"\n  [{criterion.id}] {criterion.title}")
                console.print(f"    Category: {criterion.category}")
                console.print(f"    Description: {criterion.description}")

    _run_async(_overview())
