"""Shared helper functions for task commands."""

from __future__ import annotations

from collections.abc import Coroutine
from pathlib import Path
from typing import Any

import anyio
import typer
from rich.console import Console
from rich.table import Table
from sisyphus_core.core.plans.loader import resolve_current_plan_from_status
from sisyphus_core.core.plans.models import PlanDocument, Todo, WorkPlan
from sisyphus_core.core.task_manager import TaskManager

console = Console()


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
    if task.status:
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
            if child.verification_spec:
                all_verified = all(v.verified for v in child.verification_spec)
                status_display = "완료" if all_verified else "미완료"
            else:
                status_display = "완료"
            lines.append(f"  - [{status_display}] {child.id}: {child.title}")

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
            "  [cyan]●[/cyan] LLM 검증 완료: " +
            "[bold]sisyphus-speckit task verify llm-mark <verify-id> --evidence '...'[/bold]"
        )

    if needs_manual_mark:
        console.print("  [cyan]●[/cyan] 수동 검증 시작: [bold]sisyphus-speckit task verify manual[/bold]")
        console.print(
            "  [cyan]●[/cyan] 수동 검증 완료: " +
            "[bold]sisyphus-speckit task verify manual-mark <verify-id> --evidence '...'[/bold]"
        )

    console.print("\n  [cyan]●[/cyan] 전체 검증 상태 확인: [bold]sisyphus-speckit plan status[/bold]")


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
