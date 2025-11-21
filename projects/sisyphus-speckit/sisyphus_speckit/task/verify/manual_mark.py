"""Manual verification marking command."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Annotated, Any

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


def verify_manual_mark(
    verify_id: Annotated[str, typer.Argument(help="Verification item ID")],
    evidence: Annotated[str, typer.Option("--evidence", help="Evidence description")],
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory")] = None,
) -> None:
    """Mark manual verification as completed with evidence."""
    if len(evidence) < 100:
        raise typer.BadParameter(
            "증거(evidence)는 최소 100자 이상이어야 합니다.\n\n"
            + "이유: 철저한 검증은 상세한 기록을 통해 품질을 보장합니다.\n\n"
            + "좋은 예시:\n"
            + '"Chrome 120.0 환경에서 로그인 플로우 테스트 완료. 5개 계정으로 테스트, '
            + "비밀번호 재설정 확인, 이메일 알림 수신 확인, 30분 후 세션 타임아웃 동작 검증. "
            + '모든 에러 핸들링 정상 작동."\n\n'
            + "가이드: 더 많은 검증을 수행하고 상세히 기록해주세요."
        )

    async def _mark() -> None:
        agent_name = os.getenv("ANTHROPIC_CLI_AGENT_NAME", "").lower()
        if "executor" in agent_name:
            console.print("[red]❌ ILLEGAL: Executor agents cannot run verification commands.[/red]")
            console.print("[yellow]⚠️  Verification commands are ONLY for orchestrator agents.[/yellow]\n")
            console.print("[dim]Executors are for task execution only.[/dim]")
            console.print("[dim]Manual verification must be done by the orchestrator (you, the user).[/dim]\n")
            console.print("[cyan]If you are the orchestrator:[/cyan]")
            console.print("  Run this command directly from Claude Code CLI, not through executor.\n")
            raise typer.Exit(1)

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
                            if verify_item.bash or verify_item.deterministic_bash:
                                has_unverified_bash = False
                                unverified_bash_list = []

                                for bash in verify_item.deterministic_bash:
                                    if not bash.verified_at:
                                        has_unverified_bash = True
                                        unverified_bash_list.append(bash.description or bash.execute)

                                if has_unverified_bash:
                                    console.print("[red]❌ Bash verification이 통과되지 않았습니다.[/red]")
                                    console.print(
                                        f"[yellow]통과되지 않은 bash: {len(unverified_bash_list)}개[/yellow]\n"
                                    )
                                    for bash_desc in unverified_bash_list:
                                        console.print(f"  • {bash_desc}")
                                    console.print("\n[cyan]다음 순서대로 진행하세요:[/cyan]")
                                    console.print("  [bold]1단계:[/bold] Bash verification 먼저 실행")
                                    console.print("     → sisyphus-speckit task verify bash")
                                    console.print("  [bold]2단계:[/bold] Manual verification (지금 시도한 명령)")
                                    console.print(
                                        f"     → sisyphus-speckit task verify manual-mark {verify_id} --evidence '...'"
                                    )
                                    console.print("  [bold]3단계:[/bold] LLM judge (필요시)")
                                    console.print("     → sisyphus-speckit task verify llm\n")
                                    raise typer.Exit(1)

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
        console.print("[green]수동 검증이 완료 표시되었습니다.[/green]")
        console.print(f"[cyan]증거:[/cyan] {evidence}")

        task_manager = TaskManager(plan_doc, plan_doc.work_plans[0].id)
        _display_remaining_verifications(task_manager)

    _run_async(_mark())
