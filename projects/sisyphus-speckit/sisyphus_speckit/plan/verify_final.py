from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import anyio
import typer
from rich.console import Console
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.utils.common import resolve_cwd

console = Console()


def verify_final_plan(
    verification_id: Annotated[str, typer.Option("--id", help="Final verification item ID")],
    evidence: Annotated[str, typer.Option("--evidence", help="Verification evidence description")],
    yaml_path: Annotated[Path, typer.Option("--file", "-f", help="YAML file path")] = Path(
        ".sisyphus/tasks/plan.yaml"
    ),
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory")] = None,
) -> None:
    async def _verify_final() -> None:
        working_dir = resolve_cwd(cwd)
        resolved_yaml = working_dir / yaml_path if not yaml_path.is_absolute() else yaml_path

        if not resolved_yaml.exists():
            console.print(f"[red]Error: File not found: {resolved_yaml}[/red]")
            raise typer.Exit(1)

        try:
            plan_doc = await load_plan(resolved_yaml)

            if not plan_doc.work_plans:
                console.print("[red]No work_plans found in plan document[/red]")
                raise typer.Exit(1)

            work_plan = plan_doc.work_plans[0]

            found = False
            for final_verify in work_plan.final_verification:
                if final_verify.id == verification_id:
                    final_verify.verified = True
                    final_verify.verified_at = datetime.now(UTC).isoformat()
                    final_verify.verification_evidence = evidence
                    found = True
                    break

            if not found:
                console.print(f"[red]❌ Final verification item not found: {verification_id}[/red]")
                raise typer.Exit(1)

            await save_plan(resolved_yaml, plan_doc)
            console.print(f"[green]✓ Final verification '{verification_id}' marked as verified[/green]")
            console.print(f"[cyan]Evidence:[/cyan] {evidence}")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    anyio.run(_verify_final)
