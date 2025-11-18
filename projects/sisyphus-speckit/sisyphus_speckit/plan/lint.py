from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from ruamel.yaml import YAML, YAMLError
from sisyphus_core.core.plan_linter import LintError, PlanLinter
from sisyphus_core.core.plans.models import PlanDocument
from sisyphus_core.utils.common import resolve_cwd

console = Console()


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
