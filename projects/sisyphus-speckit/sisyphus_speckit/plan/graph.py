from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Any, cast

import typer
from pydantic import ValidationError
from rich.console import Console
from ruamel.yaml import YAML, YAMLError
from sisyphus_core.core.graph.dependencies import build_plan_graph, detect_cycles, discover_plan_files
from sisyphus_core.core.graph.renderer import AsciiRenderer, MermaidRenderer
from sisyphus_core.core.plans.models import PlanDocument
from sisyphus_core.utils.common import resolve_cwd

console = Console()


class GraphFormat(str, Enum):
    ASCII = "ascii"
    MERMAID = "mermaid"


def show_graph(
    format: Annotated[
        GraphFormat, typer.Option("--format", "-f", help="Output format (ascii or mermaid)")
    ] = GraphFormat.ASCII,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory")] = None,
) -> None:
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
                    yaml_data: dict[str, Any] = yaml.load(f)
                try:
                    plan_doc = PlanDocument(**yaml_data)  # type: ignore[reportUnknownArgumentType]
                    for work_plan in plan_doc.work_plans:
                        plan_to_file[work_plan.id] = plan_file
                    all_plans.extend(plan_doc.work_plans)
                except ValidationError:
                    console.print(f"[yellow]Warning: Skipping {plan_file.name} (invalid v3.0 format)[/yellow]")
                    continue
        else:
            console.print(
                "[red]Error: No plan files found.[/red]\n"
                + f"Expected: {tasks_dir}/*.yaml (v3.0 format)\n"
                + "Run: sisyphus-speckit plan init .sisyphus/tasks/plan.yaml"
            )
            raise typer.Exit(1)

        if not all_plans:
            console.print("[red]Error: No valid plans found[/red]")
            raise typer.Exit(1)

        plans = cast(dict[str, Any], {plan.id: plan for plan in all_plans})
        graph = build_plan_graph(plans)  # type: ignore[arg-type,attr-defined]

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
                + "  1. Open the file(s) listed above\n"
                + "  2. Find the 'depends_on' field for each plan\n"
                + "  3. Remove one dependency to break the cycle\n"
                + "  4. Run 'sisyphus-speckit plan graph' again to verify\n"
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
