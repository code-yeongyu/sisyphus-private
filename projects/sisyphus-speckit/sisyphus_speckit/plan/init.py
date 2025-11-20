from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from ruamel.yaml import YAML
from sisyphus_core.core.plans.template import PlanTemplateGenerator
from sisyphus_core.utils.common import resolve_cwd

console = Console()


def init_plan(
    path: Annotated[Path, typer.Option("--path", "-p", help="Path where plan YAML will be created")] = Path(
        "./.sisyphus/tasks/plan.yaml"
    ),
    template: Annotated[
        str,
        typer.Option("--template", "-t", help="Template: 'minimal' or 'full' example"),
    ] = "full",
    initial_request: Annotated[
        str | None,
        typer.Option("--initial-request", "-r", help="Initial user request for user_request.original"),
    ] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory")] = None,
) -> None:
    working_dir = resolve_cwd(cwd)
    resolved_path = working_dir / path if not path.is_absolute() else path

    if resolved_path.exists():
        console.print(f"[red]Error: File already exists: {resolved_path}[/red]")
        raise typer.Exit(1)

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

    if initial_request is not None:
        doc.work_plans[0].user_request.original = initial_request

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False

    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    with resolved_path.open("w", encoding="utf-8") as f:
        yaml.dump(doc.model_dump(mode="json", by_alias=True, exclude_none=False), f)

    console.print(f"[green]✓ Plan template created: {resolved_path}[/green]")
    console.print(tip_msg)
