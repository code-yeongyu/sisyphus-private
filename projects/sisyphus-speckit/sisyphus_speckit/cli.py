"""Typer CLI for Sisyphus SpecKit - Plan and task specification tools."""

from __future__ import annotations

import typer

app = typer.Typer(name="sisyphus-speckit", help="Sisyphus Plan and Task Specification Tools")


@app.command()
def hello() -> None:
    """Placeholder command - plan and task commands will be added in future tasks."""
    typer.echo("sisyphus-speckit: Plan and task specification tools")


if __name__ == "__main__":
    app()
