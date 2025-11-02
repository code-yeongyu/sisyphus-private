from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import anyio
import sniffio
import typer
from pydantic import ValidationError
from rich.console import Console
from ruamel.yaml import YAML, YAMLError

from sisyphus.cli.common import resolve_cwd
from sisyphus.core.exporters.markdown import MarkdownExporter
from sisyphus.core.graph.dependencies import build_plan_graph, detect_cycles, discover_plan_files
from sisyphus.core.graph.renderer import AsciiRenderer, MermaidRenderer
from sisyphus.core.plan_linter import PlanLinter
from sisyphus.core.plan_loader import PlanLoader
from sisyphus.core.plan_navigator import PlanNavigator
from sisyphus.core.plans.loader import load_plan
from sisyphus.core.plans.models import PlanDocument
from sisyphus.utils.formatting import (
    OutputFormat,
    print_children,
    print_overview,
    print_references,
    print_task,
    print_verification,
)

plan_app = typer.Typer(name="plan", help="Plan management commands")
console = Console()


class GraphFormat(str, Enum):
    ASCII = "ascii"
    MERMAID = "mermaid"


@plan_app.command(name="lint")
def lint_plan(
    file_path: Path = typer.Option(
        Path("./ai-todolist.yaml"),
        "--file",
        "-f",
        help="YAML file path to lint",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    resolved_path = working_dir / file_path if not file_path.is_absolute() else file_path

    try:
        yaml = YAML()
        yaml.preserve_quotes = True

        if not resolved_path.exists():
            console.print(f"[red]Error: File not found: {resolved_path}[/red]")
            raise typer.Exit(1)

        with resolved_path.open("r", encoding="utf-8") as f:
            yaml_data = yaml.load(f)

        linter = PlanLinter({})
        errors = linter.lint(yaml_data)

        if errors:
            console.print(f"[red]✗ Validation failed: {len(errors)} error(s)[/red]\n")
            for error in errors:
                console.print(f"  [red]•[/red] {linter.format_error(error)}")
            raise typer.Exit(1)
        else:
            console.print("[green]✓ YAML validation passed. 0 errors.[/green]")

    except YAMLError as e:
        console.print(f"[red]YAML parsing error:[/red]\n{e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@plan_app.command(name="overview")
def show_overview(
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Show work plan overview."""
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()

        print_overview(plan, format=OutputFormat.RICH if rich else OutputFormat.PLAIN)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@plan_app.command(name="init")
def init_plan(
    path: Path = typer.Option(
        Path("./ai-todolist.yaml"),
        "--path",
        "-p",
        help="Path where plan YAML will be created",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Initialize new plan YAML template."""
    working_dir = resolve_cwd(cwd)
    resolved_path = working_dir / path if not path.is_absolute() else path

    if resolved_path.exists():
        console.print(f"[red]Error: File already exists: {resolved_path}[/red]")
        raise typer.Exit(1)

    now = datetime.now(UTC).isoformat()

    template = {
        "metadata": {
            "created_at": now,
            "updated_at": now,
            "format_version": "2.1",
        },
        "user_request": {
            "original": "TODO: Describe your project goal here",
            "created_at": now,
            "additional": [],
        },
        "objectives": {
            "core": "TODO: Core objective",
            "detailed": [],
        },
        "background": {
            "current_situation": "TODO: Current state",
            "reason_for_change": "TODO: Why change is needed",
            "changes_to_make": "TODO: What needs to change",
        },
        "required_background": {
            "description": "TODO: Required context",
            "file_structure": None,
            "references": [],
        },
        "status": {
            "execution": {
                "started": False,
                "completed": False,
                "started_at": None,
                "completed_at": None,
            },
            "work_mode": {
                "parallel_requested": False,
                "current_task_id": None,
            },
            "progress": {
                "total_tasks": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
            },
            "current_work": "",
        },
        "workflow": {
            "dependency_diagram": "",
            "critical_path": [],
        },
        "todos": [],
        "success_vision": {
            "user_perspective": [],
            "business_perspective": [],
            "technical_criteria": [],
        },
        "final_verification": [],
    }

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False

    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    with resolved_path.open("w", encoding="utf-8") as f:
        yaml.dump(template, f)

    console.print(f"[green]✓ Plan template created: {resolved_path}[/green]")


@plan_app.command(name="graph")
def show_graph(
    format: GraphFormat = typer.Option(
        GraphFormat.ASCII,
        "--format",
        "-f",
        help="Output format (ascii or mermaid)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display plan dependency graph."""
    working_dir = resolve_cwd(cwd)
    tasks_dir = working_dir / ".sisyphus" / "tasks"

    try:
        yaml = YAML()
        all_plans = []
        plan_to_file = {}

        if tasks_dir.exists():
            plan_files = discover_plan_files(working_dir)
            if not plan_files:
                console.print(f"[red]Error: No YAML files found in {tasks_dir}[/red]")
                raise typer.Exit(1)

            for plan_file in plan_files:
                with plan_file.open("r", encoding="utf-8") as f:
                    yaml_data = yaml.load(f)
                try:
                    plan_doc = PlanDocument(**yaml_data)
                    for work_plan in plan_doc.work_plans:
                        plan_to_file[work_plan.id] = plan_file
                    all_plans.extend(plan_doc.work_plans)
                except ValidationError:
                    console.print(f"[yellow]Warning: Skipping {plan_file.name} (invalid v3.0 format)[/yellow]")
                    continue
        else:
            plan_path = working_dir / "ai-todolist.yaml"

            if not plan_path.exists():
                console.print(
                    f"[red]Error: No plan files found.[/red]\n"
                    f"Expected either:\n"
                    f"  - {tasks_dir}/*.yaml (v3.0 format)\n"
                    f"  - {plan_path} (v2.1 format)"
                )
                raise typer.Exit(1)

            with plan_path.open("r", encoding="utf-8") as f:
                yaml_data = yaml.load(f)

            try:
                plan_doc = PlanDocument(**yaml_data)
                for work_plan in plan_doc.work_plans:
                    plan_to_file[work_plan.id] = plan_path
                all_plans.extend(plan_doc.work_plans)
            except ValidationError:
                console.print(
                    "[yellow]Warning: File is not v3.0 format. Graph command requires v3.0 with depends_on.[/yellow]"
                )
                raise typer.Exit(1)

        if not all_plans:
            console.print("[red]Error: No valid plans found[/red]")
            raise typer.Exit(1)

        plans = {plan.id: plan for plan in all_plans}
        graph = build_plan_graph(plans)

        cycles = detect_cycles(graph)
        if cycles:
            console.print("[red]✗ Circular dependency detected![/red]\n")
            for i, cycle in enumerate(cycles, 1):
                console.print(f"[yellow]Cycle {i}:[/yellow]")
                for j, plan_id in enumerate(cycle):
                    file_path = plan_to_file.get(plan_id, Path("unknown"))
                    relative_path = file_path.relative_to(working_dir) if file_path != Path("unknown") else file_path
                    arrow = " → " if j < len(cycle) - 1 else " → (loops back to start)"
                    console.print(f"  {plan_id:<20} [dim](in {relative_path})[/dim]{arrow}")
                console.print()

            console.print(
                "[yellow]How to fix:[/yellow]\n"
                "  1. Open the file(s) listed above\n"
                "  2. Find the 'depends_on' field for each plan\n"
                "  3. Remove one dependency to break the cycle\n"
                "  4. Run 'sisyphus plan graph' again to verify\n"
            )
            raise typer.Exit(1)

        if format == GraphFormat.ASCII:
            renderer = AsciiRenderer()
            output = renderer.render(graph)
        else:
            renderer = MermaidRenderer()
            output = renderer.render(graph)

        console.print(output)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except YAMLError as e:
        console.print(f"[red]YAML parsing error:[/red]\n{e}")
        raise typer.Exit(1)


@plan_app.command(name="get")
def get_plan_info(
    what: str = typer.Argument(..., help="What to get: task, reference"),
    current: bool = typer.Option(False, "--current", help="Get current task"),
    next_task: bool = typer.Option(False, "--next", help="Get next pending task"),
    task_id: str | None = typer.Option(None, "--id", help="Specific task ID"),
    show_references: bool = typer.Option(False, "--show-references", help="Show only references"),
    show_children: bool = typer.Option(False, "--show-children", help="Show only children"),
    show_verification: bool = typer.Option(False, "--show-verification", help="Show only verification spec"),
    show_all: bool = typer.Option(False, "--show-all", help="Show complete task info (default)"),
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format (default: plain text)"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Get information from work plan."""
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"
    output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        match what:
            case "task":
                task = None
                if current:
                    task = navigator.get_current_task()
                    if task is None:
                        console.print("[yellow]작업이 시작되지 않았습니다[/yellow]")
                        raise typer.Exit(0)
                elif next_task:
                    task = navigator.get_next_task()
                    if task is None:
                        console.print("[green]모든 작업이 완료되었습니다![/green]")
                        raise typer.Exit(0)
                elif task_id:
                    task = navigator.find_todo_by_id(task_id)
                    if task is None:
                        console.print(f"[red]작업 ID를 찾을 수 없습니다: {task_id}[/red]")
                        raise typer.Exit(1)
                else:
                    console.print("[red]--current, --next, --id 중 하나를 선택하세요[/red]")
                    raise typer.Exit(1)

                if show_references:
                    refs = navigator.get_task_references(task.id)
                    print_references(refs, format=output_format)
                elif show_children:
                    children = navigator.get_task_children(task.id)
                    print_children(children, format=output_format)
                elif show_verification:
                    verifications = navigator.get_task_verification(task.id)
                    print_verification(verifications, format=output_format)
                else:
                    print_task(task, format=output_format)

            case "reference":
                console.print("[yellow]Reference lookup not yet implemented[/yellow]")
                raise typer.Exit(1)

            case _:
                console.print(f"[red]Unknown option: {what}[/red]")
                raise typer.Exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except ValidationError as e:
        console.print(f"[red]YAML 검증 실패:[/red]\n{e}")
        raise typer.Exit(1)


@plan_app.command(name="export")
def export_plan(
    yaml_path: Path = typer.Argument(..., help="Path to YAML plan file"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output Markdown file path (default: stdout)"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Export WorkPlan YAML to Markdown format."""

    working_dir = resolve_cwd(cwd)
    resolved_yaml = working_dir / yaml_path if not yaml_path.is_absolute() else yaml_path

    if not resolved_yaml.exists():
        console.print(f"[red]Error: File not found: {resolved_yaml}[/red]")
        raise typer.Exit(1)

    async def _load_and_export() -> str:
        try:
            plan_doc = await load_plan(resolved_yaml)
            return MarkdownExporter.export(plan_doc)
        except Exception as e:
            console.print(f"[red]Error loading plan:[/red] {e}")
            raise typer.Exit(1)

    try:
        # Check if already in async context (pytest-anyio)
        try:
            sniffio.current_async_library()
            # Already in async context - use anyio.from_thread.run_sync
            markdown = anyio.from_thread.run_sync(_load_and_export)
        except sniffio.AsyncLibraryNotFoundError:
            # Not in async context, use anyio.run
            markdown = anyio.run(_load_and_export)

        if output:
            resolved_output = working_dir / output if not output.is_absolute() else output
            resolved_output.parent.mkdir(parents=True, exist_ok=True)
            resolved_output.write_text(markdown, encoding="utf-8")
            console.print(f"[green]✓ Markdown exported to: {resolved_output}[/green]")
        else:
            print(markdown)

    except Exception as e:
        console.print(f"[red]Export failed:[/red] {e}")
        raise typer.Exit(1)
