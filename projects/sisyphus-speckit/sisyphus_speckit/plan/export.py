from __future__ import annotations

from pathlib import Path

import anyio
import typer
from rich.console import Console
from sisyphus_core.core.exporters.markdown import MarkdownExporter
from sisyphus_core.core.plans.loader import load_plan
from sisyphus_core.utils.common import resolve_cwd

console = Console()


def export_plan(
    yaml_path: Path = typer.Argument(..., help="Path to YAML plan file"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output Markdown file path (default: stdout)"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
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
