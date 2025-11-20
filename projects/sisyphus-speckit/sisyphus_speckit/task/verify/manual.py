"""Manual verification display command."""

from __future__ import annotations

import typer
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import (
    _display_remaining_verifications,
    _load_current_plan,
    _run_async,
    console,
)


def verify_manual(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),  # pyright: ignore[reportCallInDefaultInitializer]
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
