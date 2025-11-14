"""Typer CLI for Sisyphus SpecKit - Plan and task specification tools."""

from __future__ import annotations

import typer

from sisyphus_speckit.plan import plan_app
from sisyphus_speckit.task import task_app

app = typer.Typer(name="sisyphus-speckit", help="sisyphus-speckit plan and Task Specification Tools")

app.add_typer(plan_app)
app.add_typer(task_app)


if __name__ == "__main__":
    app()
