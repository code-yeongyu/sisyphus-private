"""LLM verification marking command."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import typer
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.status.manager import StatusManager
from sisyphus_core.core.task_manager import TaskManager
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import (
    _display_remaining_verifications,
    _run_async,
    console,
)


def verify_llm_mark(
    verify_id: str = typer.Argument(..., help="Verification item ID"),
    evidence: str = typer.Option(..., "--evidence", help="Evidence description"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Mark LLM verification as completed with evidence."""

    async def _mark() -> None:
        working_dir = resolve_cwd(cwd)
        status_path = working_dir / ".sisyphus" / "status.json"

        status_manager = StatusManager(status_path)
        status = await status_manager.get()

        if status.current_plan is None:
            console.print("[red]현재 활성화된 작업 계획이 없습니다.[/red]")
            raise typer.Exit(1)

        plan_path = working_dir / status.current_plan.plan_path
        plan_doc = await load_plan(plan_path)

        found = False
        for work_plan in plan_doc.work_plans:

            def search_todos(todos: list[Any]) -> None:
                nonlocal found
                for todo in todos:
                    for verify_item in todo.verification_spec:
                        if verify_item.id == verify_id:
                            verify_item.verified = True
                            verify_item.verified_at = datetime.now(UTC).isoformat()
                            verify_item.orchestrator_manually_verified = True
                            verify_item.manual_verification_evidence = evidence
                            found = True
                            return
                    if todo.children:
                        search_todos(todo.children)

            search_todos(work_plan.todos)
            if found:
                break

        if not found:
            console.print(f"[red]검증 ID를 찾을 수 없습니다: {verify_id}[/red]")
            raise typer.Exit(1)

        await save_plan(plan_path, plan_doc)
        console.print("[green]LLM 검증이 완료 표시되었습니다.[/green]")
        console.print(f"[cyan]증거:[/cyan] {evidence}")

        task_manager = TaskManager(plan_doc, plan_doc.work_plans[0].id)
        _display_remaining_verifications(task_manager)

    _run_async(_mark())
