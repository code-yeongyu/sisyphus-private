"""Typer CLI for Sisyphus multi-agent system."""

from __future__ import annotations

import typer

app = typer.Typer(name="sisyphus", help="Sisyphus Multi-Agent System")

from .cli.reset import reset_app  # noqa: E402
from .cli.work import clean_history, ignore, run  # noqa: E402

_ = app.command(name="work")(run)
_ = app.command(name="ignore")(ignore)
_ = app.command(name="clean-history")(clean_history)

app.add_typer(reset_app)

if __name__ == "__main__":
    app()
