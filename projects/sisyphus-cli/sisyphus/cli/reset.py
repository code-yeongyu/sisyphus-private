from __future__ import annotations

import shutil

import typer
from rich.console import Console
from sisyphus_core.utils.common import resolve_cwd

reset_app = typer.Typer(name="reset", help="Reset Sisyphus state")
console = Console()


@reset_app.callback(invoke_without_command=True)
def reset_command(
    _ctx: typer.Context,
    include_task_specs: bool = typer.Option(  # pyright: ignore[reportCallInDefaultInitializer]
        False, "--include-task-specs", help="Also delete .sisyphus/tasks/ and status.json"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deleted without deleting"),  # pyright: ignore[reportCallInDefaultInitializer]
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),  # pyright: ignore[reportCallInDefaultInitializer]
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),  # pyright: ignore[reportCallInDefaultInitializer]
) -> None:
    working_dir = resolve_cwd(cwd)

    base_targets = [
        working_dir / "notepad.md",
        working_dir / "sessions",
        working_dir / "logs",
    ]

    task_spec_targets = [
        working_dir / ".sisyphus" / "tasks",
        working_dir / ".sisyphus" / "status.json",
    ]

    targets = base_targets + (task_spec_targets if include_task_specs else [])

    existing_targets = [t for t in targets if t.exists()]

    if not existing_targets:
        console.print("[yellow]No files or directories to delete.[/yellow]")
        return

    console.print("[bold]The following will be deleted:[/bold]\n")
    for target in existing_targets:
        target_type = "📁 Directory" if target.is_dir() else "📄 File"
        console.print(f"  {target_type}: [cyan]{target.relative_to(working_dir)}[/cyan]")

    if dry_run:
        console.print("\n[yellow]Dry run mode - nothing was deleted.[/yellow]")
        return

    if not yes:
        console.print()
        confirm = typer.confirm("Are you sure you want to delete these files?")
        if not confirm:
            console.print("[yellow]Operation cancelled.[/yellow]")
            raise typer.Exit(0)

    console.print()
    for target in existing_targets:
        try:
            if target.is_dir():
                shutil.rmtree(target)
                console.print(f"[green]✓[/green] Deleted directory: [cyan]{target.relative_to(working_dir)}[/cyan]")
            elif target.is_file():
                target.unlink()
                console.print(f"[green]✓[/green] Deleted file: [cyan]{target.relative_to(working_dir)}[/cyan]")
        except (PermissionError, OSError) as e:
            console.print(f"[red]✗[/red] Failed to delete [cyan]{target.relative_to(working_dir)}[/cyan]: {e}")

    console.print("\n[bold green]Reset complete![/bold green]")
