"""Typer CLI for Sisyphus multi-agent system."""

from __future__ import annotations

import typer

app = typer.Typer(name="sisyphus", help="Sisyphus Multi-Agent System")

from sisyphus.cli.plan import plan_app  # noqa: E402
from sisyphus.cli.reset import reset_app  # noqa: E402
from sisyphus.cli.task import task_app  # noqa: E402
from sisyphus.cli.work import clean_history, ignore, run  # noqa: E402

app.command(name="work")(run)
app.command(name="ignore")(ignore)
app.command(name="clean-history")(clean_history)

app.add_typer(plan_app)
app.add_typer(task_app)
app.add_typer(reset_app)

if __name__ == "__main__":
    app()
