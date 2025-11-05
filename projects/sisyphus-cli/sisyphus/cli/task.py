"""DEPRECATED: v2.1 task commands.

All task commands have been removed in v3.0.
Use v3.0 plan commands instead:
- sisyphus plan init
- sisyphus plan lint
- sisyphus plan graph
"""

from __future__ import annotations

import typer
from rich.console import Console

task_app = typer.Typer(name="task", help="DEPRECATED: v2.1 commands removed")
console = Console()

verify_app = typer.Typer(name="verify", help="DEPRECATED: v2.1 commands removed")
task_app.add_typer(verify_app)


def _show_deprecated_message() -> None:
    console.print("[red]ERROR: This command is deprecated (v2.1 only) and has been removed.[/red]")
    console.print("[yellow]Use v3.0 commands instead:[/yellow]")
    console.print("  sisyphus plan init    - Create new YAML plan")
    console.print("  sisyphus plan lint    - Validate plan")
    console.print("  sisyphus plan graph   - Visualize dependencies")
    raise typer.Exit(1)


@task_app.command(name="show")
def show_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    rich: bool = typer.Option(False, "--rich"),
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@task_app.command(name="current")
def show_current(
    rich: bool = typer.Option(False, "--rich"),
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@task_app.command(name="next")
def show_next(
    rich: bool = typer.Option(False, "--rich"),
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@task_app.command(name="previous")
def show_previous(
    rich: bool = typer.Option(False, "--rich"),
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@task_app.command(name="continue")
def continue_work(
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@verify_app.command(name="bash")
def verify_bash(
    cwd: str | None = typer.Option(None, "--cwd"),
    evidence: str | None = typer.Option(None, "--evidence"),
) -> None:
    _show_deprecated_message()


@verify_app.command(name="llm")
def verify_llm(
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@verify_app.command(name="llm-mark")
def verify_llm_mark(
    verify_id: str = typer.Argument(...),
    evidence: str = typer.Option(..., "--evidence"),
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@verify_app.command(name="manual")
def verify_manual(
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@verify_app.command(name="manual-mark")
def verify_manual_mark(
    verify_id: str = typer.Argument(...),
    evidence: str = typer.Option(..., "--evidence"),
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()


@verify_app.command(name="status")
def verify_status(
    cwd: str | None = typer.Option(None, "--cwd"),
) -> None:
    _show_deprecated_message()
