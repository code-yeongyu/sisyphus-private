from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.scalarstring import LiteralScalarString
from sisyphus_core.core.plan_linter import LintError, PlanLinter
from sisyphus_core.core.plans.models import PlanDocument
from sisyphus_core.utils.common import resolve_cwd

console = Console()


def _fix_multiline_texts(obj: object) -> object:
    """재귀적으로 multiline 텍스트를 pipeline(|) 형식으로 변환합니다."""
    match obj:
        case dict() as d:
            result: dict[str, object] = {}
            for key, value in d.items():
                result[key] = _fix_multiline_texts(value)
            return result
        case list() as lst:
            return [_fix_multiline_texts(item) for item in lst]
        case str() as s:
            if "\n" in s and s.count("\n") >= 1:
                return LiteralScalarString(s)
            return s
        case _:
            return obj


def _add_missing_fields(obj: object) -> object:
    """재귀적으로 nullable 필드(evidence 등)를 빈 문자열로 추가합니다."""
    match obj:
        case dict() as d:
            result: dict[str, object] = {}
            for key, value in d.items():
                result[key] = _add_missing_fields(value)
            return result
        case list() as lst:
            return [_add_missing_fields(item) for item in lst]
        case _:
            return obj


def lint_plan(
    file_path: Path = typer.Option(  # pyright: ignore[reportCallInDefaultInitializer]
        Path("./.sisyphus/tasks/plan.yaml"),
        "--file",
        "-f",
        help="YAML file path to lint",
    ),
    fix: bool = typer.Option(False, "--fix", help="Auto-fix multiline texts to pipeline format"),  # pyright: ignore[reportCallInDefaultInitializer]
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),  # pyright: ignore[reportCallInDefaultInitializer]
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

        if fix:
            yaml_data = _fix_multiline_texts(yaml_data)
            yaml_data = _add_missing_fields(yaml_data)

        try:
            plan_doc = PlanDocument(**yaml_data)  # pyright: ignore
        except Exception as e:
            console.print(f"[red]Schema validation failed:[/red]\n{e}")
            raise typer.Exit(1)

        if fix:
            with resolved_path.open("w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f)
            console.print(f"[green]✓ Fixed and saved: {resolved_path}[/green]")

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
