"""Typer CLI for Sisyphus multi-agent system."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

import anyio
import typer

from sisyphus.agents.claude import ClaudeAgent
from sisyphus.agents.droid import DroidAgent
from sisyphus.agents.opencode import OpenCodeAgent
from sisyphus.core.loop import ExecutionLoop
from sisyphus.core.prompts import PromptResolver
from sisyphus.core.session import SessionStore
from sisyphus.core.tasks import TaskValidator
from sisyphus.ui.base import create_ui
from sisyphus.utils.logging import LoggerFactory

if TYPE_CHECKING:
    from sisyphus.agents.base import Agent
    from sisyphus.ui.base import UIProtocol

app = typer.Typer(name="sisyphus", help="Sisyphus Multi-Agent System")


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
        agent_spec: "claude" | "claude:sonnet" | "droid:gpt-5" | "opencode"
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
        case "droid":
            return cast("Agent", DroidAgent(binary=binary_path, model=model))
        case "opencode":
            return cast("Agent", OpenCodeAgent(binary=binary_path, server_url=opencode_url))
        case _:
            raise typer.BadParameter(f"Unknown agent type: {agent_type}")


async def _main(
    execute_agent: Agent,
    verify_agent: Agent | None,
    execute_prompt_spec: str,
    verify_prompt_spec: str | None,
    execute_extra: str | None,
    verify_extra: str | None,
    ui: UIProtocol,
    session_store: SessionStore,
) -> None:
    """비동기 메인 함수.

    Args:
        execute_agent: Execute 에이전트
        verify_agent: Verify 에이전트 (Optional)
        execute_prompt_spec: Execute 프롬프트 spec
        verify_prompt_spec: Verify 프롬프트 spec (Optional)
        execute_extra: Execute 추가 프롬프트
        verify_extra: Verify 추가 프롬프트
        ui: UI Protocol 구현
        session_store: SessionStore 인스턴스
    """
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


@app.command(name="run")
def run(
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent type (claude|droid|opencode)"),
    execute: str | None = typer.Option(None, "--execute", help="Execute agent (AGENT[:MODEL])"),
    verify: str | None = typer.Option(None, "--verify", help="Verify agent (AGENT[:MODEL])"),
    execute_prompt: str = typer.Option(
        "prompts/execute_command.md", "--execute-prompt", help="Execute prompt (path/slash/text)"
    ),
    verify_prompt: str | None = typer.Option(
        "prompts/architect_command.md", "--verify-prompt", help="Verify prompt (path/slash/text)"
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

    execute_spec = agent if agent else execute
    verify_spec = agent if agent else verify

    if opencode_server_url:
        opencode_server_url = validate_url(opencode_server_url)

    exec_bin = resolve_binary(binary, execute_binary)
    ver_bin = resolve_binary(binary, verify_binary)

    if execute_spec is None:
        raise typer.BadParameter("Execute agent must be specified")

    execute_agent = create_agent(execute_spec, execute_sdk_options, exec_bin, opencode_server_url)
    verify_agent = create_agent(verify_spec, verify_sdk_options, ver_bin, opencode_server_url) if verify_spec else None

    ui = create_ui("cli" if no_tui else "tui")

    session_store = SessionStore()

    try:
        anyio.run(
            _main,
            execute_agent,
            verify_agent,
            execute_prompt,
            verify_prompt,
            execute_extra_prompt,
            verify_extra_prompt,
            ui,
            session_store,
        )
    except KeyboardInterrupt:
        typer.echo("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        typer.echo(f"[bold red]Error: {e}[/bold red]", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
