"""Rich formatting utilities for CLI output."""

from rich.console import Console
from rich.table import Table

from sisyphus.utils.plan_types import Todo

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
