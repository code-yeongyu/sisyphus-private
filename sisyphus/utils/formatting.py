"""Rich formatting utilities for CLI output."""

from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sisyphus.core.plan_navigator import CompletionReport
from sisyphus.utils.plan_types import ReferenceSpec, SimpleReference, Todo, VerificationItem


class OutputFormat(Enum):
    """Output format for CLI display."""

    PLAIN = "plain"
    RICH = "rich"


console = Console()


def print_task(task: Todo, format: OutputFormat = OutputFormat.PLAIN) -> None:
    """Print task with Rich formatting.

    Args:
        task: Todo object to print
        format: Output format (PLAIN or RICH)
    """
    if format == OutputFormat.PLAIN:
        output = f"Task: {task.id}\n"
        output += f"  ID: {task.id}\n"
        output += f"  Title: {task.title}\n"
        output += f"  Status: {task.status.value}\n"
        output += f"  Created: {task.created_at}\n"
        output += f"  Updated: {task.updated_at}\n"

        if task.references:
            ref_strs = []
            for ref in task.references:
                if isinstance(ref, SimpleReference):
                    ref_strs.append(ref.ref_id)
                else:
                    ref_strs.append(f"{ref.type}: {getattr(ref, 'path', getattr(ref, 'url', ref.description))}")
            output += f"  References: {', '.join(ref_strs)}\n"

        if task.children:
            children_ids = ", ".join(str(child.id) for child in task.children)
            output += f"  Children: {children_ids}\n"

        console.print(output)
    else:
        table = Table(title=f"Task: {task.id}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("ID", str(task.id))
        table.add_row("Title", task.title)
        table.add_row("Status", task.status.value)
        table.add_row("Created", task.created_at)
        table.add_row("Updated", task.updated_at)

        if task.references:
            ref_strs = []
            for ref in task.references:
                if isinstance(ref, SimpleReference):
                    ref_strs.append(ref.ref_id)
                else:
                    ref_strs.append(f"{ref.type}: {getattr(ref, 'path', getattr(ref, 'url', ref.description))}")
            table.add_row("References", ", ".join(ref_strs))

        if task.children:
            children_ids = ", ".join(str(child.id) for child in task.children)
            table.add_row("Children", children_ids)

        console.print(table)


def print_references(
    references: list[ReferenceSpec | SimpleReference], format: OutputFormat = OutputFormat.PLAIN
) -> None:
    """Print references with Rich formatting.

    Args:
        references: List of ReferenceSpec or SimpleReference objects to print
        format: Output format (PLAIN or RICH)
    """
    if not references:
        console.print("레퍼런스 없음" if format == OutputFormat.PLAIN else "[yellow]레퍼런스 없음[/yellow]")
        return

    if format == OutputFormat.PLAIN:
        output = "References:\n"
        for idx, ref in enumerate(references, 1):
            if isinstance(ref, SimpleReference):
                output += f"  {idx}. Type: Simple Ref, ID: {ref.ref_id}, Note: {ref.note or '-'}\n"
            else:
                info = getattr(ref, "path", getattr(ref, "url", getattr(ref, "code", "N/A")))
                output += f"  {idx}. Type: {ref.type}, Info: {info}, Description: {ref.description}\n"
        console.print(output)
    else:
        table = Table(title="References")
        table.add_column("Type", style="cyan")
        table.add_column("Info", style="green")
        table.add_column("Description", style="yellow")

        for ref in references:
            if isinstance(ref, SimpleReference):
                table.add_row("Simple Ref", ref.ref_id, ref.note or "-")
            else:
                info = getattr(ref, "path", getattr(ref, "url", getattr(ref, "code", "N/A")))
                if len(info) > 50:
                    info = info[:47] + "..."
                table.add_row(ref.type, info, ref.description)

        console.print(table)


def print_children(children: list[Todo], format: OutputFormat = OutputFormat.PLAIN) -> None:
    """Print child tasks with Rich formatting.

    Args:
        children: List of Todo objects (child tasks) to print
        format: Output format (PLAIN or RICH)
    """
    if not children:
        console.print("차일드 태스크 없음" if format == OutputFormat.PLAIN else "[yellow]차일드 태스크 없음[/yellow]")
        return

    if format == OutputFormat.PLAIN:
        output = "Child Tasks:\n"
        for idx, child in enumerate(children, 1):
            output += f"  {idx}. ID: {child.id}, Title: {child.title}, Status: {child.status.value}\n"
        console.print(output)
    else:
        table = Table(title="Child Tasks")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Status", style="magenta")

        for child in children:
            table.add_row(str(child.id), child.title, child.status.value)

        console.print(table)


def print_verification(verifications: list[VerificationItem], format: OutputFormat = OutputFormat.PLAIN) -> None:
    """Print verification spec with Rich formatting.

    Args:
        verifications: List of VerificationItem objects to print
        format: Output format (PLAIN or RICH)
    """
    if not verifications:
        console.print("검증 항목 없음" if format == OutputFormat.PLAIN else "[yellow]검증 항목 없음[/yellow]")
        return

    if format == OutputFormat.PLAIN:
        output = "Verification Spec:\n"
        for v in verifications:
            completed_str = "✓" if v.completed else "✗"
            output += f"  [{completed_str}] {v.id}: {v.description}\n"
        console.print(output)
    else:
        table = Table(title="Verification Spec")
        table.add_column("ID", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Completed", style="magenta")

        for v in verifications:
            completed_str = "✓" if v.completed else "✗"
            table.add_row(v.id, v.description, completed_str)

        console.print(table)


def print_completion_report(report: CompletionReport, format: OutputFormat = OutputFormat.PLAIN) -> None:
    """Print completion report with Rich formatting.

    Args:
        report: CompletionReport object to print
        format: Output format (PLAIN or RICH)
    """
    status_text = "✓ 완료 가능" if report.can_complete else "✗ 완료 불가"

    if format == OutputFormat.PLAIN:
        output = "Completion Report:\n"
        output += f"  Task ID: {report.task_id}\n"
        output += f"  현재 상태: {report.task_status.value}\n"
        output += "\n"
        output += "  차일드 태스크:\n"
        output += f"    완료: {report.children_summary['completed']}\n"
        output += f"    진행중: {report.children_summary['in_progress']}\n"
        output += f"    대기: {report.children_summary['pending']}\n"
        output += f"    → {'✓ 모두 완료' if report.all_children_completed else '✗ 미완료 있음'}\n"
        output += "\n"
        output += "  검증 항목:\n"
        output += f"    완료: {report.verification_summary['completed']} / {report.verification_summary['total']}\n"
        output += f"    → {'✓ 모두 완료' if report.all_verifications_completed else '✗ 미완료 있음'}\n"
        output += "\n"
        output += f"  {status_text}\n"
        console.print(output)
    else:
        status_color = "green" if report.can_complete else "yellow"
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
