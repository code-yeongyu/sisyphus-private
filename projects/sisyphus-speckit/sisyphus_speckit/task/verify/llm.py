"""LLM verification display command."""

from __future__ import annotations

import typer
from sisyphus_core.utils.common import resolve_cwd

from sisyphus_speckit.task._helpers import (
    _display_remaining_verifications,
    _load_current_plan,
    _run_async,
    console,
)


def verify_llm(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),  # pyright: ignore[reportCallInDefaultInitializer]
) -> None:
    """Display next LLM verification item for manual review."""

    async def _verify_llm() -> None:
        working_dir = resolve_cwd(cwd)
        _, _, task_manager = await _load_current_plan(working_dir)

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
