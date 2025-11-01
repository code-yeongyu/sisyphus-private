from __future__ import annotations

import typer
from rich.console import Console

from sisyphus.commands.common import resolve_cwd
from sisyphus.core.plan_loader import PlanLoader
from sisyphus.core.plan_navigator import PlanNavigator
from sisyphus.utils.formatting import OutputFormat, print_task

task_app = typer.Typer(name="task", help="Task execution commands")
console = Console()


@task_app.command(name="show")
def show_task(
    task_id: str = typer.Argument(..., help="Task ID to display"),
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        task = navigator.find_todo_by_id(task_id)
        if task is None:
            console.print(f"[red]작업 ID를 찾을 수 없습니다: {task_id}[/red]")
            raise typer.Exit(1)

        output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
        print_task(task, format=output_format)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@task_app.command(name="current")
def show_current(
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        task = navigator.get_current_task()
        if task is None:
            console.print("[yellow]작업이 시작되지 않았습니다[/yellow]")
            raise typer.Exit(0)

        output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
        print_task(task, format=output_format)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@task_app.command(name="next")
def show_next(
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        task = navigator.get_next_task()
        if task is None:
            console.print("[green]모든 작업이 완료되었습니다![/green]")
            raise typer.Exit(0)

        output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
        print_task(task, format=output_format)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@task_app.command(name="continue")
def continue_work(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    console.print(f"[yellow]Working directory: {working_dir}[/yellow]")
    console.print(
        "[yellow]task continue command is not yet implemented.[/yellow]\n"
        "[yellow]This command will integrate with ExecutionLoop to resume work.[/yellow]"
    )
    raise typer.Exit(1)
