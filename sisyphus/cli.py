"""Typer CLI for Sisyphus multi-agent system."""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

import anyio
import typer
from rich.console import Console

from sisyphus.agents.claude import ClaudeAgent
from sisyphus.agents.opencode import OpenCodeAgent
from sisyphus.core.loop import ExecutionLoop
from sisyphus.core.prompts import PromptResolver
from sisyphus.core.session import SessionStore
from sisyphus.core.tasks import TaskValidator
from sisyphus.ui.base import create_ui
from sisyphus.ui.tui.app import TUI, CompletionMessage, ShutdownRequestMessage
from sisyphus.utils.logging import LoggerFactory

if TYPE_CHECKING:
    from sisyphus.agents.base import Agent
    from sisyphus.ui.base import UIProtocol

app = typer.Typer(name="sisyphus", help="Sisyphus Multi-Agent System")
console = Console()
error_console = Console(stderr=True)


def validate_url(url: str) -> str:
    """URL 형식 검증.

    Args:
        url: 검증할 URL

    Returns:
        검증된 URL

    Raises:
        typer.BadParameter: URL 형식이 올바르지 않으면
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise typer.BadParameter(f"Invalid URL: {url}")
    return url


def resolve_binary(common: Path | None, specific: Path | None) -> Path | None:
    """바이너리 경로 resolve (specific > common > None).

    Args:
        common: 공통 바이너리 경로
        specific: 특정 바이너리 경로

    Returns:
        Resolved 바이너리 경로 (specific 우선, 없으면 common)
    """
    return specific if specific is not None else common


def create_agent(
    agent_spec: str,
    sdk_options_json: str | None,
    binary_path: Path | None,
    opencode_url: str | None,
) -> Agent:
    """에이전트 spec에서 에이전트 생성.

    Args:
        agent_spec: "claude" | "claude:sonnet" | "opencode"
        sdk_options_json: JSON 문자열 (SDK 옵션)
        binary_path: 바이너리 경로 (None이면 auto-detect)
        opencode_url: OpenCode 서버 URL (None이면 auto-start)

    Returns:
        Agent 인스턴스

    Raises:
        typer.BadParameter: 에이전트 타입이 알 수 없거나 JSON이 잘못되었으면
    """
    if ":" in agent_spec:
        agent_type, model = agent_spec.split(":", 1)
    else:
        agent_type, model = agent_spec, None

    try:
        sdk_options: dict[str, object] = json.loads(sdk_options_json) if sdk_options_json else {}
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"Invalid JSON in SDK options: {e}") from e

    if model:
        sdk_options["model"] = model

    match agent_type:
        case "claude":
            return cast("Agent", ClaudeAgent(model=model, sdk_options=sdk_options))
        case "opencode":
            return cast("Agent", OpenCodeAgent(binary=binary_path, server_url=opencode_url))
        case _:
            raise typer.BadParameter(f"Unknown agent type: {agent_type}")


async def _main_cli(
    execute_agent: Agent,
    verify_agent: Agent | None,
    execute_prompt_spec: str | None,
    verify_prompt_spec: str | None,
    execute_extra: str | None,
    verify_extra: str | None,
    ui: UIProtocol,
    session_store: SessionStore,
) -> None:
    """CLI 모드 메인 함수 (기존 로직).

    Args:
        execute_agent: Execute 에이전트
        verify_agent: Verify 에이전트 (Optional)
        execute_prompt_spec: Execute 프롬프트 spec (None이면 built-in 사용)
        verify_prompt_spec: Verify 프롬프트 spec (None이면 built-in 사용)
        execute_extra: Execute 추가 프롬프트
        verify_extra: Verify 추가 프롬프트
        ui: UI Protocol 구현
        session_store: SessionStore 인스턴스
    """
    start_time = time.time()

    prompt_resolver = PromptResolver()
    logger_factory = LoggerFactory()

    task_validator = TaskValidator() if Path("ai-todolist.md").exists() else None

    loop = ExecutionLoop(
        execute_agent=execute_agent,
        ui=ui,
        session_store=session_store,
        prompt_resolver=prompt_resolver,
        logger_factory=logger_factory,
        verify_agent=verify_agent,
        task_validator=task_validator,
    )

    await loop.run(
        execute_prompt=execute_prompt_spec,
        execute_extra=execute_extra,
        verify_prompt=verify_prompt_spec,
        verify_extra=verify_extra,
    )

    elapsed_seconds = time.time() - start_time
    hours = int(elapsed_seconds // 3600)
    minutes = int((elapsed_seconds % 3600) // 60)
    secs = int(elapsed_seconds % 60)

    time_parts = []
    if hours > 0:
        time_parts.append(f"{hours}시간")
    if minutes > 0:
        time_parts.append(f"{minutes}분")
    if secs > 0 or not time_parts:
        time_parts.append(f"{secs}초")

    elapsed_str = " ".join(time_parts)
    await ui.show_status(f"✅ 모든 작업이 완료되었습니다. (소요 시간: {elapsed_str})")
    await ui.show_status("Ctrl+C를 눌러 종료하세요.")

    try:
        shutdown_event = anyio.Event()
        await shutdown_event.wait()
    except (KeyboardInterrupt, anyio.get_cancelled_exc_class()):
        pass


async def _main_tui(
    execute_agent: Agent,
    verify_agent: Agent | None,
    execute_prompt_spec: str | None,
    verify_prompt_spec: str | None,
    execute_extra: str | None,
    verify_extra: str | None,
    ui: UIProtocol,
    session_store: SessionStore,
) -> None:
    """TUI 모드 메인 함수 (TUI와 ExecutionLoop 병렬 실행).

    Args:
        execute_agent: Execute 에이전트
        verify_agent: Verify 에이전트 (Optional)
        execute_prompt_spec: Execute 프롬프트 spec (None이면 built-in 사용)
        verify_prompt_spec: Verify 프롬프트 spec (None이면 built-in 사용)
        execute_extra: Execute 추가 프롬프트
        verify_extra: Verify 추가 프롬프트
        ui: UI Protocol 구현
        session_store: SessionStore 인스턴스
    """
    if not isinstance(ui, TUI):
        raise TypeError("ui must be TUI instance for TUI mode")

    async def monitor_shutdown(tg: anyio.abc.TaskGroup) -> None:
        """Shutdown 이벤트 모니터링 (TUI → ExecutionLoop 종료)."""
        await ui.shutdown_event.wait()
        tg.cancel_scope.cancel()

    async def run_execution_loop() -> None:
        """ExecutionLoop 실행 (TUI 준비 완료 후)."""

        start_time = time.time()

        try:
            # TUI 준비 대기 (타임아웃 10초)
            with anyio.move_on_after(10.0) as cancel_scope:
                await ui.ready_event.wait()

            if cancel_scope.cancelled_caught:
                raise TimeoutError("TUI initialization timeout")

            prompt_resolver = PromptResolver()
            logger_factory = LoggerFactory()
            task_validator = TaskValidator() if Path("ai-todolist.md").exists() else None

            if isinstance(ui, TUI):
                ui.set_task_validator(task_validator)

            loop = ExecutionLoop(
                execute_agent=execute_agent,
                ui=ui,
                session_store=session_store,
                prompt_resolver=prompt_resolver,
                logger_factory=logger_factory,
                verify_agent=verify_agent,
                task_validator=task_validator,
            )

            await loop.run(
                execute_prompt=execute_prompt_spec,
                execute_extra=execute_extra,
                verify_prompt=verify_prompt_spec,
                verify_extra=verify_extra,
            )

            elapsed_seconds = time.time() - start_time
            ui.post_message(CompletionMessage("모든 작업이 완료되었습니다.", elapsed_seconds=elapsed_seconds))

            try:
                completion_event = anyio.Event()
                await completion_event.wait()
            except (KeyboardInterrupt, anyio.get_cancelled_exc_class()):
                pass
        except Exception as e:
            # 에러를 UI에 표시하고 종료 요청
            try:
                await ui.show_status(f"[bold red]Error: {e}[/bold red]")
            except Exception:
                pass
            ui.post_message(ShutdownRequestMessage())
            raise  # TaskGroup이 다른 task도 취소하도록 재발생

    try:
        async with anyio.create_task_group() as tg:
            # TUI 시작 (백그라운드)
            tg.start_soon(ui.run_async)
            # ExecutionLoop 시작 (TUI 준비 후)
            tg.start_soon(run_execution_loop)
            # Shutdown 모니터링 (별도 task)
            tg.start_soon(monitor_shutdown, tg)
    except* (SystemExit, KeyboardInterrupt):
        # 정상 종료 (Ctrl+C 등) - ExceptionGroup 처리
        pass
    except* Exception as eg:
        for e in eg.exceptions:
            error_console.print("\n[bold red]═══ Unhandled Error ═══[/bold red]")
            error_console.print(f"[red]Type: {type(e).__name__}[/red]")
            error_console.print(f"[red]Message: {e}[/red]")
            error_console.print("\n[yellow]Traceback:[/yellow]")
            traceback.print_exception(type(e), e, e.__traceback__)
        raise typer.Exit(1)


@app.command(name="run")
def run(
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent type (claude|opencode)"),
    execute: str | None = typer.Option(None, "--execute", help="Execute agent (AGENT[:MODEL])"),
    verify: str | None = typer.Option(None, "--verify", help="Verify agent (AGENT[:MODEL])"),
    execute_prompt: str | None = typer.Option(
        None, "--execute-prompt", help="Execute prompt (path/slash/text, default: built-in)"
    ),
    verify_prompt: str | None = typer.Option(
        None, "--verify-prompt", help="Verify prompt (path/slash/text, default: built-in)"
    ),
    execute_extra_prompt: str | None = typer.Option(None, "--execute-extra-prompt", help="Extra execute prompt"),
    verify_extra_prompt: str | None = typer.Option(None, "--verify-extra-prompt", help="Extra verify prompt"),
    binary: Path | None = typer.Option(None, "--binary", help="Common binary path"),
    execute_binary: Path | None = typer.Option(None, "--execute-binary", help="Execute binary (overrides --binary)"),
    verify_binary: Path | None = typer.Option(None, "--verify-binary", help="Verify binary (overrides --binary)"),
    execute_sdk_options: str | None = typer.Option(None, "--execute-sdk-options", help="Execute SDK options (JSON)"),
    verify_sdk_options: str | None = typer.Option(None, "--verify-sdk-options", help="Verify SDK options (JSON)"),
    opencode_server_url: str | None = typer.Option(None, "--opencode-server-url", help="OpenCode server URL"),
    no_tui: bool = typer.Option(False, "--no-tui", help="Disable TUI, use CLI mode"),
    log: Path | None = typer.Option(None, "--log", help="Log file path"),
) -> None:
    """Run Sisyphus multi-agent system."""
    if agent and (execute or verify):
        raise typer.BadParameter("Cannot use --agent with --execute or --verify")

    if not agent and not execute:
        agent = "claude"

    if agent:
        execute_spec = agent
        verify_spec = agent
    else:
        execute_spec = execute if execute else "claude"
        verify_spec = verify if verify else execute_spec

    if opencode_server_url:
        opencode_server_url = validate_url(opencode_server_url)

    exec_bin = resolve_binary(binary, execute_binary)
    ver_bin = resolve_binary(binary, verify_binary)

    if execute_spec is None:
        raise typer.BadParameter("Execute agent must be specified")

    execute_agent = create_agent(execute_spec, execute_sdk_options, exec_bin, opencode_server_url)
    verify_agent = create_agent(verify_spec, verify_sdk_options, ver_bin, opencode_server_url) if verify_spec else None

    # DEBUG: verify_agent 생성 확인
    console.print(f"[yellow]DEBUG: verify_spec={verify_spec}, verify_agent={verify_agent}[/yellow]")

    ui = create_ui("cli" if no_tui else "tui")

    session_store = SessionStore()

    try:
        if no_tui:
            # CLI 모드 (trio/asyncio 자동 선택 - backend 미지정)
            anyio.run(
                _main_cli,
                execute_agent,
                verify_agent,
                execute_prompt,
                verify_prompt,
                execute_extra_prompt,
                verify_extra_prompt,
                ui,
                session_store,
            )
        else:
            # TUI 모드 (Textual은 asyncio만 지원)
            anyio.run(
                _main_tui,
                execute_agent,
                verify_agent,
                execute_prompt,
                verify_prompt,
                execute_extra_prompt,
                verify_extra_prompt,
                ui,
                session_store,
                backend="asyncio",
            )
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        error_console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
