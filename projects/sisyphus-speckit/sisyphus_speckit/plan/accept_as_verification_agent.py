from __future__ import annotations

import anyio
import typer
from rich.console import Console
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.operations import mark_verification_agent_checklist
from sisyphus_core.core.status.manager import StatusManager
from sisyphus_core.utils.common import resolve_cwd

console = Console()


def accept_as_verification_agent(
    checklist_id: str = typer.Option(..., "--id", help="Acceptance criteria checklist ID"),
    evidence: str = typer.Option(..., "--evidence", help="Evidence of completion"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    async def _accept() -> None:
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

        success, message = mark_verification_agent_checklist(work_plan, checklist_id, evidence)

        if not success:
            console.print(f"[red]❌ {message}[/red]")
            raise typer.Exit(1)

        await save_plan(plan_path, plan_doc)
        console.print(f"[green]✓ {message}[/green]")
        console.print(f"[cyan]증거:[/cyan] {evidence}")

    anyio.run(_accept)
