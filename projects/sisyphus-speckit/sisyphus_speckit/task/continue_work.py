"""Continue work command - complete current task and move to next."""

from __future__ import annotations

from datetime import UTC, datetime

import typer
from rich.panel import Panel
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.models import Todo, TodoStatus
from sisyphus_core.core.status.manager import StatusManager
from sisyphus_core.core.task_manager import TaskManager
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import (
    _display_verification_status_table,
    _format_task_display,
    _run_async,
    console,
)


def continue_work(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Continue work: complete current task and move to next, or start first task."""

    async def _continue() -> None:
        working_dir = resolve_cwd(cwd)
        status_path = working_dir / ".sisyphus" / "status.json"

        status_manager = StatusManager(status_path)
        status = await status_manager.get()

        if status.current_plan is None:
            console.print("[red]현재 작업 계획이 없습니다.[/red]")
            raise typer.Exit(1)

        plan_path = working_dir / status.current_plan.plan_path
        plan_doc = await load_plan(plan_path)

        if not plan_doc.work_plans:
            console.print("[red]작업 계획에 work_plans가 없습니다.[/red]")
            raise typer.Exit(1)

        work_plan = plan_doc.work_plans[0]
        task_manager = TaskManager(plan_doc, work_plan.id)

        if not work_plan.execution.started:
            first_task = task_manager.get_next_task()
            if first_task is None:
                console.print("[yellow]실행할 작업이 없습니다.[/yellow]")
                return

            work_plan.execution.started = True
            work_plan.execution.started_at = datetime.now(UTC).isoformat()
            work_plan.work_mode.current_task_id = first_task.id
            first_task.status = TodoStatus.in_progress

            await save_plan(plan_path, plan_doc)

            console.print("[green]작업을 시작합니다.[/green]")
            display = _format_task_display(first_task)
            console.print(Panel(display, title="시작된 작업", border_style="green"))
            return

        current_task = task_manager.get_current_task()
        if current_task is None:
            all_todos: list[Todo] = []

            def collect_all_todos(todos: list[Todo]) -> None:
                for todo in todos:
                    all_todos.append(todo)
                    if todo.children:
                        collect_all_todos(todo.children)

            collect_all_todos(work_plan.todos)

            if len(all_todos) > 0:
                all_completed = all(t.computed_status == TodoStatus.completed for t in all_todos)

                all_verified = True
                for todo in all_todos:
                    if todo.verification_spec:
                        report = task_manager.check_task_completion(todo.id)
                        if not report.can_complete:
                            all_verified = False
                            break

                if all_completed and all_verified:
                    console.print("[green]모든 작업이 완료되었습니다! 🎉[/green]")
                    console.print("[yellow]다음 명령으로 plan을 완료 처리하세요:[/yellow]")
                    console.print("[cyan]  sisyphus-speckit plan mark completed[/cyan]")
                    return

            console.print("[yellow]진행 중인 작업이 없습니다.[/yellow]")
            return

        report = task_manager.check_task_completion(current_task.id)
        if not report.can_complete:
            console.print("[red]❌ 다음 작업으로 넘어갈 수 없습니다.[/red]")
            console.print("[dim]완료 조건을 만족하지 못했습니다:[/dim]\n")

            # 1. 하위 작업 완료 체크
            if not report.all_children_completed:
                completed = report.children_summary["completed"]
                total = sum(report.children_summary.values())
                console.print(f"[yellow]❌ 하위 작업 미완료: {completed}/{total} 완료[/yellow]")
                console.print(
                    "[dim]   → 모든 하위 작업을 완료한 후, 검증항목을 모두 통과 시킨 후 다시 시도하세요[/dim]\n"
                )

            if current_task.verification_spec:
                console.print("[bold yellow]📋 검증 순서 (반드시 순차적으로 진행):[/bold yellow]")
                console.print("  [cyan]1단계:[/cyan] 수동 검증 (Manual Evidence) - 100자 이상 증거 필수")
                console.print("  [cyan]2단계:[/cyan] Bash 자동 검증")
                console.print("  [cyan]3단계:[/cyan] LLM Judge 검증\n")

                for verify_item in current_task.verification_spec:
                    if not verify_item.verified:
                        if (
                            not verify_item.orchestrator_manually_verified
                            or not verify_item.manual_verification_evidence
                        ):
                            console.print(f"[red]❌ [{verify_item.id}] {verify_item.title}[/red]")
                            console.print(
                                f"[yellow]   → 1단계: 수동 검증 미완료[/yellow] "
                                f"(orchestrator_manually_verified={verify_item.orchestrator_manually_verified}, "
                                f"evidence={'있음' if verify_item.manual_verification_evidence else '없음'})"
                            )
                            console.print(
                                f"[cyan]   sisyphus-speckit task verify manual-mark {verify_item.id} "
                                f"--evidence '<상세한 검증 증거 100자 이상>'[/cyan]\n"
                            )
                            continue

                        if verify_item.bash:
                            console.print(f"[yellow]⚠️  [{verify_item.id}] {verify_item.title}[/yellow]")
                            console.print("[green]   ✓ 1단계: 수동 검증 완료[/green]")
                            console.print("[yellow]   → 2단계: Bash 자동 검증 미완료[/yellow]")
                            console.print("[cyan]   sisyphus-speckit task verify bash[/cyan]\n")
                            continue

                        if verify_item.llm_judge:
                            console.print(f"[yellow]⚠️  [{verify_item.id}] {verify_item.title}[/yellow]")
                            console.print("[green]   ✓ 1단계: 수동 검증 완료[/green]")
                            if verify_item.bash:
                                console.print("[green]   ✓ 2단계: Bash 자동 검증 완료[/green]")
                            console.print("[yellow]   → 3단계: LLM Judge 검증 미완료[/yellow]")
                            console.print("[cyan]   sisyphus-speckit task verify llm[/cyan]")
                            console.print(
                                f"[cyan]   sisyphus-speckit task verify llm-mark {verify_item.id} "
                                f"--evidence '<증거 설명>'[/cyan]\n"
                            )
                            continue

            if not report.all_verifications_completed or not report.all_manual_verifications_completed:
                console.print("\n[bold cyan]━━━ 전체 검증 상태 ━━━[/bold cyan]")
                _display_verification_status_table(work_plan, task_manager, show_current_task=False)

            raise typer.Exit(1)

        # CRITICAL: Validate 3 conditions BEFORE marking task as completed
        # Note: acceptance_criteria is NOT checked here - it's only for verification agent
        deterministic_bash_errors: list[str] = []
        manual_verification_errors: list[str] = []
        llm_judge_errors: list[str] = []

        # 1. deterministic_bash 모두 verified_at 존재
        for verify_item in current_task.verification_spec:
            for bash in verify_item.deterministic_bash:
                if not bash.verified_at:
                    deterministic_bash_errors.append(f"[{verify_item.id}] '{bash.description}'")

        # 2. manual 검증 모두 통과 (orchestrator_manually_verified)
        for verify_item in current_task.verification_spec:
            if not verify_item.orchestrator_manually_verified:
                manual_verification_errors.append(f"[{verify_item.id}] '{verify_item.title}'")

        # 3. llm_judge 검증 모두 통과 (빈 리스트는 통과)
        for verify_item in current_task.verification_spec:
            for llm_judge in verify_item.llm_judge:
                if not verify_item.verified:
                    llm_judge_errors.append(f"[{verify_item.id}] '{verify_item.title}'")
                    break

        has_errors = deterministic_bash_errors or manual_verification_errors or llm_judge_errors

        if has_errors:
            console.print("[red]✗ 작업 완료 불가능 - 다음 검증이 누락되었습니다:[/red]\n")

            if deterministic_bash_errors:
                console.print("[bold yellow]Deterministic Bash 검증 미완료:[/bold yellow]")
                for error in deterministic_bash_errors:
                    console.print(f"  [yellow]• {error}[/yellow]")
                console.print("\n[cyan]명령어:[/cyan] sisyphus-speckit task verify bash\n")

            if manual_verification_errors:
                console.print("[bold yellow]수동 검증 미완료:[/bold yellow]")
                for error in manual_verification_errors:
                    console.print(f"  [yellow]• {error}[/yellow]")
                console.print("\n[cyan]명령어:[/cyan] sisyphus-speckit task verify manual --evidence <증거>\n")

            if llm_judge_errors:
                console.print("[bold yellow]LLM Judge 검증 미완료:[/bold yellow]")
                for error in llm_judge_errors:
                    console.print(f"  [yellow]• {error}[/yellow]")
                console.print("\n[cyan]명령어:[/cyan] sisyphus-speckit task verify llm\n")

            raise typer.Exit(1)

        current_task.status = TodoStatus.completed

        next_task = task_manager.get_next_task(current_task.id)

        if next_task is None:
            work_plan.work_mode.current_task_id = None

            await save_plan(plan_path, plan_doc)

            console.print("[green]모든 작업이 완료되었습니다! 🎉[/green]")
            console.print("[yellow]다음 명령으로 plan을 완료 처리하세요:[/yellow]")
            console.print("[cyan]  sisyphus-speckit plan mark completed[/cyan]")
            return

        next_task.status = TodoStatus.in_progress
        work_plan.work_mode.current_task_id = next_task.id

        await save_plan(plan_path, plan_doc)

        console.print(f"[green]작업 '{current_task.title}'을(를) 완료했습니다.[/green]")
        console.print("[yellow]다음 작업으로 이동합니다.[/yellow]")
        display = _format_task_display(next_task)
        console.print(Panel(display, title="다음 작업", border_style="green"))
        console.print("\n[bold yellow]⚠️  주의:[/bold yellow]")
        console.print("[yellow]'sisyphus-executor'를 호출해서 다음 작업을 진행하세요.[/yellow]")
        console.print("[yellow]절대로 직접 진행하지 마세요.[/yellow]")

    _run_async(_continue())
