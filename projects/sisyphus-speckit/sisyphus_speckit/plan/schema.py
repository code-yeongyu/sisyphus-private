from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax
from sisyphus_core.core.plans.models import PlanDocument

console = Console()


def plan_schema(
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Display or save the JSON schema for PlanDocument.

    The schema defines the structure and validation rules for YAML plan files.
    Can be used with tools that support JSON Schema validation.
    """
    schema = PlanDocument.model_json_schema()
    json_str = json.dumps(schema, indent=2, ensure_ascii=False)

    if output:
        _ = output.write_text(json_str, encoding="utf-8")
        console.print(f"[green]✓[/green] Schema saved to {output}")
    else:
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        console.print(syntax)
