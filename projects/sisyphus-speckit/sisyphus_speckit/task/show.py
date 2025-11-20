from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.panel import Panel
from rich.table import Table
from sisyphus_core.core.plans.models import ReferenceItem, Todo
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _format_task_display, _load_current_plan, _run_async, console

if TYPE_CHECKING:
    from sisyphus_core.core.plans.models import WorkPlan


def _resolve_reference(ref_id: str, global_refs: list[ReferenceItem]) -> ReferenceItem | None:
    """Resolve a reference ID from global references list."""
    for ref in global_refs:
        if ref.ref_id == ref_id:
            return ref
    return None


def _display_children_recursively(children: list[Todo], indent: int = 0) -> None:
    """Display task children recursively with proper indentation."""
    for child in children:
        prefix = "  " * indent
        status_display = "✓ Completed" if child.computed_status.value == "completed" else "⊙ Pending"
        console.print(f"{prefix}- [{child.id}] {child.title} ({status_display})")
        if child.children:
            _display_children_recursively(child.children, indent + 1)


def _display_verification_specs(task: Todo) -> None:
    """Display verification specifications in detail."""
    if not task.verification_spec:
        return

    console.print("\n[bold cyan]Verification Specifications:[/bold cyan]")

    # Create table for overview
    vspec_table = Table(show_header=True, header_style="bold magenta")
    vspec_table.add_column("ID", style="cyan")
    vspec_table.add_column("Title", style="green")
    vspec_table.add_column("Status", style="yellow")
    vspec_table.add_column("Bash", style="blue")
    vspec_table.add_column("LLM Judge", style="blue")

    for vspec in task.verification_spec:
        bash_count = len(vspec.bash) if vspec.bash else 0
        llm_count = len(vspec.llm_judge) if vspec.llm_judge else 0
        verified_str = "[green]✓ Verified[/green]" if vspec.verified else "[red]✗ Not Verified[/red]"

        vspec_table.add_row(
            vspec.id,
            vspec.title or "N/A",
            verified_str,
            f"({bash_count})" if bash_count > 0 else "",
            f"({llm_count})" if llm_count > 0 else "",
        )

    console.print(vspec_table)

    # Display detailed information
    console.print("\n[bold cyan]Detailed Verification Information:[/bold cyan]")
    for vspec in task.verification_spec:
        console.print(f"\n  [yellow]{vspec.id}[/yellow] - {vspec.title or 'N/A'}")
        if vspec.description:
            console.print(f"    Description: {vspec.description}")
        console.print(f"    Status: {'✓ Verified' if vspec.verified else '✗ Not Verified'}")

        if vspec.bash:
            console.print(f"    Bash checks: {len(vspec.bash)}")
            for bash in vspec.bash:
                console.print(f"      - Execute: {bash.execute}")
                if bash.expected_exit_code is not None:
                    console.print(f"        Expected exit code: {bash.expected_exit_code}")
                if bash.notes:
                    console.print(f"        Notes: {bash.notes}")

        if vspec.llm_judge:
            console.print(f"    LLM judges: {len(vspec.llm_judge)}")
            for llm in vspec.llm_judge:
                console.print(f"      - By: {llm.by}")
                if llm.instruction:
                    console.print(f"        Instruction: {llm.instruction[:100]}...")


async def _show_task_impl(task: Todo, work_plan: WorkPlan, working_dir: Path) -> None:
    """Internal implementation to display task details (reusable by other commands)."""
    # Display basic task information
    display = _format_task_display(task, show_children=False, show_verification=False)
    console.print(Panel(display, title=f"작업 {task.id}", border_style="cyan"))

    # 1. Display verification specifications in detail
    _display_verification_specs(task)

    # 2. Display children recursively
    if task.children:
        console.print("\n[bold cyan]Sub-tasks:[/bold cyan]")
        _display_children_recursively(task.children, indent=1)

    # 3. Display and resolve references
    if task.references:
        console.print("\n[bold cyan]References:[/bold cyan]")
        for ref in task.references:
            if ref.ref_id:
                # Resolve from global references
                global_ref = _resolve_reference(ref.ref_id, work_plan.references)
                if global_ref:
                    ref_content = global_ref.uri or (global_ref.inline[:100] if global_ref.inline else "N/A")
                    console.print(f"  - [{ref.ref_id}]: {ref_content}")
                else:
                    console.print(f"  - [{ref.ref_id}]: (unresolved)")
            elif ref.uri:
                console.print(f"  - URI: {ref.uri}")
            elif ref.inline:
                content = ref.inline[:100] + "..." if len(ref.inline) > 100 else ref.inline
                console.print(f"  - Inline: {content}")

    status_file = working_dir / ".sisyphus" / "status.json"
    try:
        status_content = json.loads(status_file.read_text())
        plan_path_str = status_content.get("current_plan", {}).get("plan_path")
        if plan_path_str:
            plan_file_path = working_dir / plan_path_str
            try:
                relative_path = plan_file_path.relative_to(Path.cwd())
            except ValueError:
                relative_path = plan_file_path
            console.print(f"\n[bold cyan]Plan File:[/bold cyan] {relative_path}")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass


def show_task(
    task_id: Annotated[str, typer.Argument(help="Task ID")],
    _rich: Annotated[bool, typer.Option("--rich", help="Rich formatting (legacy option, always enabled)")] = False,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory")] = None,
) -> None:
    async def _show() -> None:
        working_dir = resolve_cwd(cwd)
        _, work_plan, task_manager = await _load_current_plan(working_dir)

        task = task_manager.find_todo_by_id(task_id)
        if task is None:
            console.print(f"[red]작업 ID를 찾을 수 없습니다: {task_id}[/red]")
            raise typer.Exit(1)

        await _show_task_impl(task, work_plan, working_dir)

    _run_async(_show())
