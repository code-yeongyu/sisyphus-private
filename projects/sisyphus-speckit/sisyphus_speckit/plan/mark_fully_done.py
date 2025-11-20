from __future__ import annotations

from typing import Annotated

import anyio
import typer
from rich.console import Console
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.operations import mark_fully_done
from sisyphus_core.core.status.manager import StatusManager
from sisyphus_core.utils.common import resolve_cwd

console = Console()


def mark_fully_done_command(
    evidence: Annotated[str, typer.Option("--evidence", help="Evidence of full completion")],
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory")] = None,
) -> None:
    async def _mark_fully_done() -> None:
        working_dir = resolve_cwd(cwd)
        status_path = working_dir / ".sisyphus" / "status.json"

        status_manager = StatusManager(status_path)
        status = await status_manager.get()

        if status.current_plan is None:
            console.print("[red]현재 활성화된 작업 계획이 없습니다.[/red]")
            raise typer.Exit(1)

        plan_path = working_dir / status.current_plan.plan_path
        plan_doc = await load_plan(plan_path)

        if not plan_doc.work_plans:
            console.print("[red]작업 계획에 work_plans가 없습니다.[/red]")
            raise typer.Exit(1)

        work_plan = plan_doc.work_plans[0]

        success, message = mark_fully_done(work_plan, evidence)

        if not success:
            console.print(f"[red]❌ {message}[/red]")
            raise typer.Exit(1)

        await save_plan(plan_path, plan_doc)
        console.print(f"[green]✓ {message}[/green]")
        console.print(f"[cyan]증거:[/cyan] {evidence}")
        console.print(f"[cyan]완료 시각:[/cyan] {work_plan.execution.fully_done_at}")

    anyio.run(_mark_fully_done)
