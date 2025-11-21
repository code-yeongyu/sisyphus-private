"""Shared display utilities for sisyphus-speckit CLI."""

from __future__ import annotations

import json

from rich.console import Console
from sisyphus_core.utils.common import resolve_cwd

console = Console()


def display_current_plan() -> None:
    """Display current plan file context.

    This function should be called at the start of command functions
    to display which plan file is currently being worked on.
    """
    try:
        working_dir = resolve_cwd(None)
        status_path = working_dir / ".sisyphus" / "status.json"

        if not status_path.exists():
            return  # No status file, skip display

        # Use synchronous file read (StatusManager is async, but we need sync here)
        with open(status_path, encoding="utf-8") as f:
            status_data = json.load(f)

        if status_data.get("current_plan"):
            plan_path = status_data["current_plan"]["plan_path"]
            console.print(f"[dim]Working on:[/dim] [cyan]{plan_path}[/cyan]")
    except Exception:
        # Gracefully handle any errors
        pass
