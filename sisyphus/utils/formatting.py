"""Rich formatting utilities for CLI output."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sisyphus.core.plan_navigator import CompletionReport
from sisyphus.utils.plan_types import SimpleReference, Todo, VerificationItem

console = Console()


def print_task(task: Todo) -> None:
    """Print task with Rich formatting.

    Args:
        task: Todo object to print
    """
    table = Table(title=f"Task: {task.id}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("ID", task.id)
    table.add_row("Title", task.title)
    table.add_row("Status", task.status.value)
    table.add_row("Created", task.created_at)
    table.add_row("Updated", task.updated_at)

    if task.references:
        refs = ", ".join(ref.ref_id for ref in task.references)
        table.add_row("References", refs)

    if task.children:
        children_ids = ", ".join(child.id for child in task.children)
        table.add_row("Children", children_ids)

    console.print(table)


def print_references(references: list[SimpleReference]) -> None:
    """Print references with Rich formatting.

    Args:
        references: List of SimpleReference objects to print
    """
    if not references:
        console.print("[yellow]레퍼런스 없음[/yellow]")
        return

    table = Table(title="References")
    table.add_column("Ref ID", style="cyan")
    table.add_column("Note", style="green")

    for ref in references:
        table.add_row(ref.ref_id, ref.note or "-")

    console.print(table)


def print_children(children: list[Todo]) -> None:
    """Print child tasks with Rich formatting.

    Args:
        children: List of Todo objects (child tasks) to print
    """
    if not children:
        console.print("[yellow]차일드 태스크 없음[/yellow]")
        return

    table = Table(title="Child Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Status", style="magenta")

    for child in children:
        table.add_row(child.id, child.title, child.status.value)

    console.print(table)


def print_verification(verifications: list[VerificationItem]) -> None:
    """Print verification spec with Rich formatting.

    Args:
        verifications: List of VerificationItem objects to print
    """
    if not verifications:
        console.print("[yellow]검증 항목 없음[/yellow]")
        return

    table = Table(title="Verification Spec")
    table.add_column("ID", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Completed", style="magenta")

    for v in verifications:
        completed_str = "✓" if v.completed else "✗"
        table.add_row(v.id, v.description, completed_str)

    console.print(table)


def print_completion_report(report: CompletionReport) -> None:
    """Print completion report with Rich formatting.

    Args:
        report: CompletionReport object to print
    """
    if report.can_complete:
        status_color = "green"
        status_text = "✓ 완료 가능"
    else:
        status_color = "yellow"
        status_text = "✗ 완료 불가"

    lines = [
        f"[bold]Task ID:[/bold] {report.task_id}",
        f"[bold]현재 상태:[/bold] {report.task_status.value}",
        "",
        "[bold]차일드 태스크:[/bold]",
        f"  완료: {report.children_summary['completed']}",
        f"  진행중: {report.children_summary['in_progress']}",
        f"  대기: {report.children_summary['pending']}",
        f"  → {'✓ 모두 완료' if report.all_children_completed else '✗ 미완료 있음'}",
        "",
        "[bold]검증 항목:[/bold]",
        f"  완료: {report.verification_summary['completed']} / {report.verification_summary['total']}",
        f"  → {'✓ 모두 완료' if report.all_verifications_completed else '✗ 미완료 있음'}",
        "",
        f"[{status_color}][bold]{status_text}[/bold][/{status_color}]",
    ]

    panel = Panel(
        "\n".join(lines),
        title="Completion Report",
        border_style=status_color,
    )
    console.print(panel)
