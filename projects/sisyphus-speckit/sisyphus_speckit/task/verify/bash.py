"""Bash verification command for task verification."""

from __future__ import annotations

from datetime import UTC, datetime

import anyio
import typer
from rich.console import Console
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.status.manager import StatusManager
from sisyphus_core.core.task_manager import TaskManager
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import _display_remaining_verifications, _run_async

console = Console()


def verify_bash(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),  # pyright: ignore[reportCallInDefaultInitializer]
    _evidence: str | None = typer.Option(  # pyright: ignore[reportCallInDefaultInitializer]
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

        if not verify_item.bash and not verify_item.deterministic_bash:
            if verify_item.orchestrator_judge:
                console.print("[yellow]orchestrator_judge 검증은 수동 확인이 필요합니다.[/yellow]")
                console.print("[dim]orchestrator_judge는 LLM 기반 판단으로, CLI에서 자동 실행되지 않습니다.[/dim]")
            else:
                console.print("[yellow]bash 또는 deterministic_bash 검증 항목이 없습니다.[/yellow]")
            return

        all_passed = True

        # Process regular bash verifications
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

        for det_bash_item in verify_item.deterministic_bash:
            console.print(f"\n[cyan]Deterministic 실행:[/cyan] {det_bash_item.execute}")

            result = await anyio.run_process(
                ["bash", "-c", det_bash_item.execute],
                check=False,
                cwd=str(working_dir),
            )

            passed = True
            if result.returncode != det_bash_item.expected_exit_code:
                expected_code = det_bash_item.expected_exit_code
                got_code = result.returncode
                console.print(f"[red]✗ exit code 불일치[/red] (expected: {expected_code}, got: {got_code})")
                passed = False

            stdout_decoded = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
            stderr_decoded = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

            if det_bash_item.expected_stdout is not None:
                if stdout_decoded.strip() != det_bash_item.expected_stdout.strip():
                    console.print("[red]✗ stdout 불일치[/red]")
                    console.print(f"[dim]expected:[/dim]\n{det_bash_item.expected_stdout}")
                    console.print(f"[dim]got:[/dim]\n{stdout_decoded}")
                    passed = False

            if det_bash_item.expected_stderr is not None:
                if stderr_decoded.strip() != det_bash_item.expected_stderr.strip():
                    console.print("[red]✗ stderr 불일치[/red]")
                    console.print(f"[dim]expected:[/dim]\n{det_bash_item.expected_stderr}")
                    console.print(f"[dim]got:[/dim]\n{stderr_decoded}")
                    passed = False

            if passed:
                console.print(f"[green]✓ 성공[/green] (exit code: {result.returncode})")
                det_bash_item.verified_at = datetime.now(UTC).isoformat()
            else:
                all_passed = False

            if stdout_decoded and det_bash_item.expected_stdout is None:
                console.print(f"[dim]출력:[/dim]\n{stdout_decoded}")

            if stderr_decoded and det_bash_item.expected_stderr is None:
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
