"""Task navigation and verification commands for v3.0 YAML plans.

Provides commands to navigate through tasks, check status, and manage verification.
All commands work with .sisyphus/tasks/*.yaml plans (v3.0 format).
"""

from __future__ import annotations

from collections.abc import Coroutine
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import anyio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sisyphus_core.core.plans.loader import (
    load_plan,
    resolve_current_plan_from_status,
    save_plan,
)
from sisyphus_core.core.plans.models import (
    PlanDocument,
    Todo,
    TodoStatus,
    WorkPlan,
)
from sisyphus_core.core.status.manager import StatusManager
from sisyphus_core.core.task_manager import TaskManager
from sisyphus_core.utils.common import resolve_cwd

task_app = typer.Typer(name="task", help="Task navigation and verification commands")
console = Console()

verify_app = typer.Typer(name="verify", help="Verification management commands")
task_app.add_typer(verify_app)


def _run_async(coro: Coroutine[Any, Any, None]) -> None:
    """Synchronous wrapper for async functions.

    Note: anyio.run() expects a coroutine function, not a coroutine object.
    We wrap the coroutine in a lambda to make it work.
    """
    anyio.run(lambda: coro)


async def _load_current_plan(
    working_dir: Path,
) -> tuple[PlanDocument, WorkPlan, TaskManager]:
    """Load current plan from status.json."""
    plan_doc = await resolve_current_plan_from_status(working_dir)
    if plan_doc is None:
        console.print("[red]현재 활성화된 작업 계획이 없습니다.[/red]")
        console.print("[yellow]다음 명령으로 계획을 활성화하세요:[/yellow]")
        console.print("  sisyphus-speckit plan init")
        raise typer.Exit(1)

    if not plan_doc.work_plans:
        console.print("[red]작업 계획에 work_plans가 없습니다.[/red]")
        raise typer.Exit(1)

    work_plan = plan_doc.work_plans[0]
    return plan_doc, work_plan, TaskManager(plan_doc, work_plan.id)


def _format_task_display(
    task: Todo,
    show_children: bool = True,
    show_verification: bool = True,
) -> str:
    """Format task information for display."""
    lines = []
    lines.append(f"[bold cyan]작업 ID:[/bold cyan] {task.id}")
    lines.append(f"[bold cyan]제목:[/bold cyan] {task.title}")
    lines.append(f"[bold cyan]상태:[/bold cyan] {task.status.value}")

    if task.description:
        lines.append(f"[bold cyan]설명:[/bold cyan] {task.description}")

    if task.references:
        lines.append("[bold cyan]참조:[/bold cyan]")
        for ref in task.references:
            if ref.ref_id:
                lines.append(f"  - ref_id: {ref.ref_id}")
            elif ref.uri:
                lines.append(f"  - uri: {ref.uri}")
            elif ref.inline:
                lines.append(f"  - inline: {ref.inline}")

    if show_children and task.children:
        lines.append(f"[bold cyan]하위 작업:[/bold cyan] {len(task.children)}개")
        for child in task.children:
            lines.append(f"  - [{child.status.value}] {child.id}: {child.title}")

    if show_verification and task.verification_spec:
        verified_count = sum(1 for v in task.verification_spec if v.verified)
        total_count = len(task.verification_spec)
        lines.append(f"[bold cyan]검증:[/bold cyan] {verified_count}/{total_count} 완료")

    return "\n".join(lines)


def _display_verification_guidance(current_task: Todo) -> None:
    """Display verification commands based on remaining verification types."""
    if not current_task.verification_spec:
        return

    unverified = [v for v in current_task.verification_spec if not v.verified]
    if not unverified:
        return

    has_bash = any(v.bash for v in unverified)
    has_llm = any(v.llm_judge for v in unverified)
    needs_manual_mark = any(not v.orchestrator_manually_verified for v in unverified)

    console.print("\n[bold yellow]📋 다음 검증 단계:[/bold yellow]")

    if has_bash:
        console.print("  [cyan]●[/cyan] Bash 자동 검증: [bold]sisyphus-speckit task verify bash[/bold]")

    if has_llm:
        console.print("  [cyan]●[/cyan] LLM 검증 확인: [bold]sisyphus-speckit task verify llm[/bold]")
        console.print(
            "  [cyan]●[/cyan] LLM 검증 완료: "
            "[bold]sisyphus-speckit task verify llm-mark <verify-id> --evidence '...'[/bold]"
        )

    if needs_manual_mark:
        console.print("  [cyan]●[/cyan] 수동 검증 시작: [bold]sisyphus-speckit task verify manual[/bold]")
        console.print(
            "  [cyan]●[/cyan] 수동 검증 완료: "
            "[bold]sisyphus-speckit task verify manual-mark <verify-id> --evidence '...'[/bold]"
        )

    console.print("\n  [cyan]●[/cyan] 전체 검증 상태 확인: [bold]sisyphus-speckit task verify status[/bold]")


def _display_verification_status_table(
    work_plan: WorkPlan,
    task_manager: TaskManager,
    show_current_task: bool = True,
) -> None:
    if show_current_task:
        current_task = task_manager.get_current_task()
        if current_task:
            all_tasks_dfs = []

            def collect_tasks_dfs(todos: list[Any]) -> None:
                for todo in todos:
                    all_tasks_dfs.append(todo)
                    if todo.children:
                        collect_tasks_dfs(todo.children)

            collect_tasks_dfs(work_plan.todos)

            try:
                current_index = next(i for i, t in enumerate(all_tasks_dfs) if t.id == current_task.id)
                task_position = f"{current_index + 1}/{len(all_tasks_dfs)}"
            except StopIteration:
                task_position = "?/?"

            console.print(f"[bold green]현재 작업:[/bold green] {task_position} - {current_task.title}")
            console.print(f"[dim]작업 ID: {current_task.id}[/dim]\n")
        else:
            console.print("[yellow]진행 중인 작업이 없습니다.[/yellow]\n")

    all_verifications: list[tuple[str, str, Any]] = []

    def collect_verifications(todos: list[Any], prefix: str = "") -> None:
        for todo in todos:
            for verify_item in todo.verification_spec:
                all_verifications.append((f"{prefix}{todo.title}", verify_item.title, verify_item))
            if todo.children:
                collect_verifications(todo.children, prefix=f"{prefix}{todo.title} > ")

    collect_verifications(work_plan.todos)

    if not all_verifications:
        console.print("[yellow]검증 항목이 없습니다.[/yellow]")
        return

    verified_count = sum(1 for _, _, item in all_verifications if item.verified)
    total_count = len(all_verifications)
    manual_verified_count = sum(1 for _, _, item in all_verifications if item.orchestrator_manually_verified)

    console.print(f"[cyan]검증 상태: {verified_count}/{total_count} 완료[/cyan]")
    console.print(f"[magenta]수동 검증: {manual_verified_count}/{total_count} 완료[/magenta]\n")

    table = Table(title="검증 목록")
    table.add_column("작업", style="cyan")
    table.add_column("검증 항목", style="yellow")
    table.add_column("타입", style="blue")
    table.add_column("상태", style="green")
    table.add_column("Orchestrator 수동검증", style="magenta")
    table.add_column("증거", style="dim")

    for task_title, verify_title, verify_item in all_verifications:
        verify_types = []
        if verify_item.bash:
            verify_types.append("bash")
        if verify_item.llm_judge:
            verify_types.append("llm")
        if not verify_item.bash and not verify_item.llm_judge:
            verify_types.append("manual")

        verify_type_str = ", ".join(verify_types) if verify_types else "unknown"

        status_emoji = "✓" if verify_item.verified else "○"
        status_color = "green" if verify_item.verified else "yellow"

        manual_verified_emoji = "✓" if verify_item.orchestrator_manually_verified else "✗"
        manual_verified_color = "green" if verify_item.orchestrator_manually_verified else "red"

        evidence_status = "있음" if verify_item.manual_verification_evidence else "없음"
        evidence_color = "green" if verify_item.manual_verification_evidence else "dim"

        table.add_row(
            task_title,
            verify_title,
            verify_type_str,
            f"[{status_color}]{status_emoji}[/{status_color}]",
            f"[{manual_verified_color}]{manual_verified_emoji}[/{manual_verified_color}]",
            f"[{evidence_color}]{evidence_status}[/{evidence_color}]",
        )

    console.print(table)

    remaining = total_count - verified_count
    if remaining > 0:
        console.print(f"\n[yellow]남은 검증: {remaining}개[/yellow]")
    else:
        console.print("\n[green]모든 검증이 완료되었습니다! ✓[/green]")


def _display_remaining_verifications(task_manager: TaskManager) -> None:
    current_task = task_manager.get_current_task()
    if current_task is None:
        return

    if not current_task.verification_spec:
        console.print("\n[green]검증 항목이 없습니다.[/green]")
        return

    unverified_items = [v for v in current_task.verification_spec if not v.verified]
    total_count = len(current_task.verification_spec)
    remaining_count = len(unverified_items)
    verified_count = total_count - remaining_count

    console.print(f"\n[cyan]검증 진행 상황: {verified_count}/{total_count} 완료[/cyan]")

    if remaining_count == 0:
        console.print("[green]✓ 모든 검증이 완료되었습니다![/green]")
        console.print("[yellow]다음 명령으로 작업을 계속하세요:[/yellow]")
        console.print("  [bold cyan]sisyphus-speckit task continue[/bold cyan]")
    else:
        console.print(f"[yellow]남은 검증: {remaining_count}개[/yellow]\n")
        console.print("[bold cyan]미완료 검증 항목:[/bold cyan]")
        for idx, verify_item in enumerate(unverified_items, 1):
            console.print(f"  [{idx}] {verify_item.title}")
            if verify_item.description:
                console.print(f"      {verify_item.description}")


@task_app.command(name="show")
def show_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    rich: bool = typer.Option(
        False,
        "--rich",
        help="Rich formatting (legacy option, always enabled)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display specific task by ID."""

    async def _show() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        task = task_manager.find_todo_by_id(task_id)
        if task is None:
            console.print(f"[red]작업 ID를 찾을 수 없습니다: {task_id}[/red]")
            raise typer.Exit(1)

        display = _format_task_display(task)
        console.print(Panel(display, title=f"작업 {task_id}", border_style="cyan"))

    _run_async(_show())


@task_app.command(name="current")
def show_current(
    rich: bool = typer.Option(
        False,
        "--rich",
        help="Rich formatting (legacy option, always enabled)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display currently in-progress task."""

    async def _current() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        current_task = task_manager.get_current_task()
        if current_task is None:
            console.print("[yellow]작업이 시작되지 않았습니다.[/yellow]")
            console.print("다음 명령으로 작업을 시작하세요: [cyan]sisyphus-speckit task continue[/cyan]")
            return

        display = _format_task_display(current_task)
        console.print(Panel(display, title="현재 작업", border_style="green"))

    _run_async(_current())


@task_app.command(name="next")
def show_next(
    rich: bool = typer.Option(
        False,
        "--rich",
        help="Rich formatting (legacy option, always enabled)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display next pending task."""

    async def _next() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        next_task = task_manager.get_next_task()
        if next_task is None:
            console.print("[green]모든 작업이 완료되었습니다! 🎉[/green]")
            return

        display = _format_task_display(next_task)
        console.print(Panel(display, title="다음 작업", border_style="yellow"))

    _run_async(_next())


@task_app.command(name="previous")
def show_previous(
    rich: bool = typer.Option(
        False,
        "--rich",
        help="Rich formatting (legacy option, always enabled)",
    ),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display previous task in DFS order."""

    async def _previous() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        current_task = task_manager.get_current_task()
        if current_task is None:
            console.print("[yellow]작업이 시작되지 않았습니다.[/yellow]")
            return

        previous_task = task_manager.get_previous_task()
        if previous_task is None:
            console.print("[yellow]첫 작업입니다.[/yellow]")
            return

        display = _format_task_display(previous_task)
        console.print(Panel(display, title="이전 작업", border_style="blue"))

    _run_async(_previous())


@task_app.command(name="continue")
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
            tasks_dir = working_dir / ".sisyphus" / "tasks"
            yaml_files = list(tasks_dir.glob("*.yaml")) if tasks_dir.exists() else []

            if len(yaml_files) == 1:
                plan_path = yaml_files[0]
                relative_path = plan_path.relative_to(working_dir)
                await status_manager.set_current(
                    plan_path=str(relative_path),
                    plan_root=str(tasks_dir.relative_to(working_dir)),
                )
                console.print(f"[green]작업 계획 자동 선택:[/green] {relative_path}")
            elif len(yaml_files) == 0:
                console.print("[red]현재 활성화된 작업 계획이 없습니다.[/red]")
                console.print("[yellow]다음 명령으로 계획을 활성화하세요:[/yellow]")
                console.print("  sisyphus-speckit plan init")
                raise typer.Exit(1)
            else:
                console.print("[red]현재 활성화된 작업 계획이 없습니다.[/red]")
                console.print("[yellow]여러 작업 계획이 있습니다. 다음 명령으로 하나를 선택하세요:[/yellow]")
                for yaml_file in yaml_files:
                    console.print(f"  - {yaml_file.relative_to(working_dir)}")
                console.print("\n  sisyphus-speckit plan init <plan-file>")
                raise typer.Exit(1)
        else:
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
                all_completed = all(t.status == TodoStatus.completed for t in all_todos)

                all_verified = True
                for todo in all_todos:
                    if todo.verification_spec:
                        report = task_manager.check_task_completion(todo.id)
                        if not report.can_complete:
                            all_verified = False
                            break

                if all_completed and all_verified and not work_plan.execution.completed:
                    work_plan.execution.completed = True
                    work_plan.execution.completed_at = datetime.now(UTC).isoformat()
                    await save_plan(plan_path, plan_doc)
                    console.print("[green]모든 작업이 완료되었습니다! 🎉[/green]")
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
                console.print("[dim]   → 모든 하위 작업을 완료한 후 다시 시도하세요[/dim]\n")

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

        current_task.status = TodoStatus.completed

        next_task = task_manager.get_next_task(current_task.id)

        if next_task is None:
            work_plan.execution.completed = True
            work_plan.execution.completed_at = datetime.now(UTC).isoformat()
            work_plan.work_mode.current_task_id = None

            await save_plan(plan_path, plan_doc)

            console.print("[green]모든 작업이 완료되었습니다! 🎉[/green]")
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


@task_app.command(name="accept")
def task_accept(
    criterion_id: str = typer.Option(..., "--id", help="Acceptance criterion ID"),
    evidence: str = typer.Option(..., "--evidence", help="Evidence of completion"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Mark acceptance criteria checklist as completed with evidence."""

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

        found = False
        for criteria in work_plan.acceptance_criteria_for_verification_agent:
            for checklist in criteria.checklists:
                if checklist.id == criterion_id:
                    checklist.checked_at = datetime.now(UTC).isoformat()
                    checklist.checked_evidence = evidence
                    found = True
                    break
            if found:
                break

        if not found:
            console.print(f"[red]❌ Acceptance criterion ID를 찾을 수 없습니다: {criterion_id}[/red]")
            raise typer.Exit(1)

        await save_plan(plan_path, plan_doc)
        console.print(f"[green]✓ Acceptance criterion '{criterion_id}' 마킹 완료[/green]")
        console.print(f"[cyan]증거:[/cyan] {evidence}")

    _run_async(_accept())


@verify_app.command(name="bash")
def verify_bash(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
    evidence: str | None = typer.Option(
        None,
        "--evidence",
        help="Evidence description (legacy option)",
    ),
) -> None:
    """Execute next bash verification test."""

    async def _verify_bash() -> None:
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
        task_manager = TaskManager(plan_doc, work_plan.id)

        result = task_manager.next_unverified()
        if result is None:
            console.print("[green]모든 검증이 완료되었습니다! ✓[/green]")
            return

        verify_item, current_idx, total_count = result

        console.print(f"[cyan]검증 {current_idx}/{total_count}[/cyan]")
        console.print(f"[bold]{verify_item.title}[/bold]")
        console.print(f"{verify_item.description}")

        if not verify_item.bash:
            console.print("[yellow]bash 검증 항목이 없습니다.[/yellow]")
            return

        all_passed = True
        for bash_item in verify_item.bash:
            console.print(f"\n[cyan]실행:[/cyan] {bash_item.execute}")

            result = await anyio.run_process(
                ["bash", "-c", bash_item.execute],
                check=False,
                cwd=str(working_dir),
            )

            if result.returncode == bash_item.expected_exit_code:
                console.print(f"[green]✓ 성공[/green] (exit code: {result.returncode})")
            else:
                expected_code = bash_item.expected_exit_code
                got_code = result.returncode
                console.print(f"[red]✗ 실패[/red] (expected: {expected_code}, got: {got_code})")
                all_passed = False

            if result.stdout:
                stdout_decoded = result.stdout.decode("utf-8", errors="replace")
                console.print(f"[dim]출력:[/dim]\n{stdout_decoded}")

            if result.stderr:
                stderr_decoded = result.stderr.decode("utf-8", errors="replace")
                console.print(f"[dim]오류:[/dim]\n{stderr_decoded}")

        if all_passed:
            verify_item.verified = True
            verify_item.verified_at = datetime.now(UTC).isoformat()
            await save_plan(plan_path, plan_doc)
            console.print("\n[green]검증 완료! ✓[/green]")
            _display_remaining_verifications(task_manager)
        else:
            console.print("\n[red]검증 실패. 문제를 해결한 후 다시 시도하세요.[/red]")
            _display_remaining_verifications(task_manager)
            raise typer.Exit(1)

    _run_async(_verify_bash())


@verify_app.command(name="llm")
def verify_llm(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display next LLM verification item for manual review."""

    async def _verify_llm() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        result = task_manager.next_unverified()
        if result is None:
            console.print("[green]모든 검증이 완료되었습니다! ✓[/green]")
            return

        verify_item, current_idx, total_count = result

        console.print(f"[cyan]검증 {current_idx}/{total_count}[/cyan]")
        console.print(f"[bold]{verify_item.title}[/bold]")
        console.print(f"{verify_item.description}")

        if not verify_item.llm_judge:
            console.print("[yellow]LLM 검증 항목이 없습니다.[/yellow]")
            return

        for llm_item in verify_item.llm_judge:
            console.print(f"\n[cyan]검증자:[/cyan] {llm_item.by}")
            console.print(f"[cyan]지시사항:[/cyan] {llm_item.instruction}")

            if llm_item.context_commands:
                console.print("[cyan]컨텍스트 명령:[/cyan]")
                for cmd in llm_item.context_commands:
                    console.print(f"  - {cmd}")

        verify_cmd = f"sisyphus-speckit task verify llm-mark {verify_item.id} --evidence '<증거 설명>'"
        console.print(f"\n[yellow]검증을 완료하려면:[/yellow] {verify_cmd}")

        _display_remaining_verifications(task_manager)

    _run_async(_verify_llm())


@verify_app.command(name="llm-mark")
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


@verify_app.command(name="manual")
def verify_manual(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display next manual verification item."""

    async def _verify_manual() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        result = task_manager.next_unverified()
        if result is None:
            console.print("[green]모든 검증이 완료되었습니다! ✓[/green]")
            return

        verify_item, current_idx, total_count = result

        console.print(f"[cyan]검증 {current_idx}/{total_count}[/cyan]")
        console.print(f"[bold]{verify_item.title}[/bold]")
        console.print(f"{verify_item.description}")

        console.print("\n[bold yellow]📋 검증 절차:[/bold yellow]")
        console.print("  [cyan]1.[/cyan] 초기 작업 계획서의 요구사항 확인")
        console.print("  [cyan]2.[/cyan] 실제 구현 결과 검토")
        console.print("  [cyan]3.[/cyan] 계획서대로 완료되었는지 증거 수집")
        console.print("     [dim]- 테스트 실행 결과[/dim]")
        console.print("     [dim]- 코드 변경 내역 (git diff, 파일 경로)[/dim]")
        console.print("     [dim]- 기능 동작 확인 (스크린샷, 로그, 실행 결과)[/dim]")

        verify_cmd = (
            f"sisyphus-speckit task verify manual-mark {verify_item.id} --evidence '<상세한 검증 증거 100자 이상>'"
        )
        console.print("\n[bold yellow]검증 완료 표시:[/bold yellow]")
        console.print(f"  {verify_cmd}")

        _display_remaining_verifications(task_manager)

    _run_async(_verify_manual())


@verify_app.command(name="manual-mark")
def verify_manual_mark(
    verify_id: str = typer.Argument(..., help="Verification item ID"),
    evidence: str = typer.Option(..., "--evidence", help="Evidence description"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Mark manual verification as completed with evidence."""
    if len(evidence) < 100:
        raise typer.BadParameter(
            "증거(evidence)는 최소 100자 이상이어야 합니다.\n\n"
            "이유: 철저한 검증은 상세한 기록을 통해 품질을 보장합니다.\n\n"
            "좋은 예시:\n"
            '"Chrome 120.0 환경에서 로그인 플로우 테스트 완료. 5개 계정으로 테스트, '
            "비밀번호 재설정 확인, 이메일 알림 수신 확인, 30분 후 세션 타임아웃 동작 검증. "
            '모든 에러 핸들링 정상 작동."\n\n'
            "가이드: 더 많은 검증을 수행하고 상세히 기록해주세요."
        )

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
        console.print("[green]수동 검증이 완료 표시되었습니다.[/green]")
        console.print(f"[cyan]증거:[/cyan] {evidence}")

        task_manager = TaskManager(plan_doc, plan_doc.work_plans[0].id)
        _display_remaining_verifications(task_manager)

    _run_async(_mark())


@verify_app.command(name="status")
def verify_status(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Display verification status for all tasks."""

    async def _status() -> None:
        working_dir = resolve_cwd(cwd)
        plan_doc, work_plan, task_manager = await _load_current_plan(working_dir)

        _display_verification_status_table(work_plan, task_manager, show_current_task=True)

    _run_async(_status())
