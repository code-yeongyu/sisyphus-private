from __future__ import annotations

from enum import Enum
from pathlib import Path

import anyio
import typer
from pydantic import ValidationError
from rich.console import Console
from ruamel.yaml import YAML, YAMLError

from sisyphus.cli.common import resolve_cwd
from sisyphus.core.exporters.markdown import MarkdownExporter
from sisyphus.core.graph.dependencies import build_plan_graph, detect_cycles, discover_plan_files
from sisyphus.core.graph.renderer import AsciiRenderer, MermaidRenderer
from sisyphus.core.plan_linter import LintError, PlanLinter
from sisyphus.core.plans.loader import load_plan
from sisyphus.core.plans.models import PlanDocument
from sisyphus.core.plans.template import PlanTemplateGenerator

plan_app = typer.Typer(name="plan", help="Plan management commands")
console = Console()


class GraphFormat(str, Enum):
    ASCII = "ascii"
    MERMAID = "mermaid"


@plan_app.command(name="lint")
def lint_plan(
    file_path: Path = typer.Option(
        Path("./.sisyphus/tasks/plan.yaml"),
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

        try:
            plan_doc = PlanDocument(**yaml_data)
        except Exception as e:
            console.print(f"[red]Schema validation failed:[/red]\n{e}")
            raise typer.Exit(1)

        linter = PlanLinter({})
        errors = linter.validate_all(plan_doc, resolved_path)

        if errors:
            console.print(f"[red]✗ Validation failed: {len(errors)} error(s)[/red]\n")

            by_category: dict[str, list[LintError]] = {}
            for error in errors:
                by_category.setdefault(error.category, []).append(error)

            for category, cat_errors in by_category.items():
                console.print(f"\n[yellow]{category.upper()} ERRORS:[/yellow]")
                for error in cat_errors:
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


@plan_app.command(name="init")
def init_plan(
    path: Path = typer.Option(
        Path("./.sisyphus/tasks/plan.yaml"),
        "--path",
        "-p",
        help="Path where plan YAML will be created",
    ),
    template: str = typer.Option(
        "full",
        "--template",
        "-t",
        help="Template type: 'minimal' (TODO placeholders) or 'full' (complete example)",
    ),
    initial_request: str | None = typer.Option(
        None,
        "--initial-request",
        "-r",
        help="Initial user request to populate user_request.original field",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Initialize new plan YAML template.

    Examples:
        # Create minimal template with TODO placeholders
        sisyphus plan init

        # Create full example with all fields populated
        sisyphus plan init --template full

        # Custom path
        sisyphus plan init --path .sisyphus/tasks/my-plan.yaml
    """
    working_dir = resolve_cwd(cwd)
    resolved_path = working_dir / path if not path.is_absolute() else path

    if resolved_path.exists():
        console.print(f"[red]Error: File already exists: {resolved_path}[/red]")
        raise typer.Exit(1)

    # ✅ PlanTemplateGenerator 사용 (스펙 준수 자동 보장)
    try:
        if template == "full":
            doc = PlanTemplateGenerator.full_example()
            tip_msg = (
                "[yellow]Tip: This is a full example with all fields populated.\n"
                "      Edit the values to match your project requirements.[/yellow]"
            )
        else:
            doc = PlanTemplateGenerator.minimal()
            tip_msg = (
                "[yellow]Tip: Replace TODO placeholders with your actual content.\n"
                "      Use --template full to see a complete example.[/yellow]"
            )
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Template generation failed:[/red] {e}")
        raise typer.Exit(1)

    # Populate initial request if provided
    if initial_request is not None:
        doc.work_plans[0].user_request.original = initial_request

    # YAML 저장
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False

    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    with resolved_path.open("w", encoding="utf-8") as f:
        # Use by_alias and exclude_none for clean YAML output
        # mode="json" ensures Enums are serialized as values
        yaml.dump(doc.model_dump(mode="json", by_alias=True, exclude_none=False), f)

    console.print(f"[green]✓ Plan template created: {resolved_path}[/green]")
    console.print(tip_msg)


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
            console.print(
                f"[red]Error: No plan files found.[/red]\n"
                f"Expected: {tasks_dir}/*.yaml (v3.0 format)\n"
                f"Run: sisyphus plan init .sisyphus/tasks/plan.yaml"
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
