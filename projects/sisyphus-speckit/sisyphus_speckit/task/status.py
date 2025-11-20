"""Task status display command."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _load_current_plan, _run_async

console = Console()


def task_status(
    cwd: Annotated[str | None, typer.Option("--cwd", help="Working directory")] = None,
) -> None:
    """Display current task's verification status in detail.

    Shows:
    1. Current task information
    2. All verification specifications with details (ID, title, description)
    3. Whether the task is continuable to next step
    4. Acceptance criteria if present
    """

    async def _task_status() -> None:
        working_dir = resolve_cwd(cwd)
        _, _, task_manager = await _load_current_plan(working_dir)

        current_task = task_manager.get_current_task()
        if not current_task:
            console.print("[red]현재 작업이 없습니다.[/red]")
            return

        # 1. Task 기본 정보
        console.print(
            Panel(
                f"[bold cyan]ID:[/bold cyan] {current_task.id}\n"
                + f"[bold cyan]Title:[/bold cyan] {current_task.title}\n"
                + f"[bold cyan]Status:[/bold cyan] {current_task.status.value if current_task.status else 'N/A'}\n"
                + f"[bold cyan]Description:[/bold cyan] {current_task.description or 'N/A'}",
                title="Task Information",
                border_style="cyan",
            )
        )

        # 2. Verification Spec 상세 출력
        if current_task.verification_spec:
            console.print("\n[bold cyan]Verification Specifications:[/bold cyan]")
            vspec_table = Table(show_header=True, header_style="bold magenta")
            vspec_table.add_column("ID", style="cyan")
            vspec_table.add_column("Title", style="green")
            vspec_table.add_column("Description")
            vspec_table.add_column("Verified", style="yellow")
            vspec_table.add_column("Bash", style="blue")
            vspec_table.add_column("LLM Judge", style="blue")

            for vspec in current_task.verification_spec:
                bash_str = "✓" if vspec.bash else ""
                llm_str = "✓" if vspec.llm_judge else ""
                verified_str = "[green]✓[/green]" if vspec.verified else "[red]✗[/red]"

                vspec_table.add_row(
                    vspec.id,
                    vspec.title or "",
                    vspec.description or "",
                    verified_str,
                    bash_str,
                    llm_str,
                )

            console.print(vspec_table)

            # Detailed verification spec information
            console.print("\n[bold cyan]Detailed Verification Information:[/bold cyan]")
            for vspec in current_task.verification_spec:
                console.print(f"\n[yellow]ID: {vspec.id}[/yellow]")
                console.print(f"  Title: {vspec.title or 'N/A'}")
                console.print(f"  Description: {vspec.description or 'N/A'}")
                console.print(f"  Verified: {vspec.verified}")

                if vspec.bash:
                    console.print("  [bold]Bash Checks:[/bold]")
                    for bash in vspec.bash:
                        console.print(f"    - Execute: {bash.execute}")
                        if bash.expected_exit_code is not None:
                            console.print(f"      Expected Exit Code: {bash.expected_exit_code}")
                        if bash.notes:
                            console.print(f"      Notes: {bash.notes}")

                if vspec.llm_judge:
                    console.print("  [bold]LLM Judge:[/bold]")
                    for llm in vspec.llm_judge:
                        console.print(f"    - By: {llm.by}")
                        if llm.instruction:
                            console.print(f"      Instruction: {llm.instruction[:100]}...")
        else:
            console.print("\n[yellow]검증 항목이 없습니다.[/yellow]")

        # 3. Acceptance Criteria
        if current_task.acceptance_criteria:
            console.print("\n[bold cyan]Acceptance Criteria:[/bold cyan]")
            ac_table = Table(show_header=True, header_style="bold magenta")
            ac_table.add_column("ID", style="cyan")
            ac_table.add_column("Condition")
            ac_table.add_column("Verified", style="yellow")

            for ac in current_task.acceptance_criteria:
                verified_str = "[green]✓[/green]" if ac.verified_at is not None else "[red]✗[/red]"
                ac_table.add_row(ac.id, ac.condition, verified_str)

            console.print(ac_table)

        # 4. Continuable 여부
        completion_report = task_manager.check_task_completion(current_task.id)
        can_continue = completion_report.can_complete

        continuable_str = "[green]Yes[/green]" if can_continue else "[red]No[/red]"
        console.print(f"\n[bold cyan]Continuable:[/bold cyan] {continuable_str}")

        if not can_continue:
            console.print("\n[yellow]다음 단계로 넘어가기 위해 필요한 작업:[/yellow]")

            if not completion_report.all_children_completed:
                completed = completion_report.children_summary["completed"]
                total = completed + completion_report.children_summary["pending"]
                console.print(f"  [cyan]●[/cyan] 모든 하위 작업 완료: {completed}/{total} completed")

            if not completion_report.all_verifications_completed:
                verified = completion_report.verification_summary["completed"]
                total_verif = completion_report.verification_summary["total"]
                console.print(f"  [cyan]●[/cyan] 모든 검증 항목 완료: {verified}/{total_verif} completed")

            if not completion_report.all_manual_verifications_completed:
                manual = completion_report.manual_verification_summary["completed"]
                total_manual = completion_report.manual_verification_summary["total"]
                console.print(f"  [cyan]●[/cyan] 모든 수동 검증 완료: {manual}/{total_manual} completed")

    _run_async(_task_status())
