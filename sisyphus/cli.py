"""Typer CLI for Sisyphus multi-agent system."""

from __future__ import annotations

import json
import shutil
import time
import traceback
from enum import Enum
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
from sisyphus.utils.theme import ThemeName, detect_system_theme

if TYPE_CHECKING:
    from sisyphus.agents.base import Agent
    from sisyphus.ui.base import UIProtocol

app = typer.Typer(name="sisyphus", help="Sisyphus Multi-Agent System")
console = Console()
error_console = Console(stderr=True)


class ThemeOption(str, Enum):
    """TUI theme options."""

    SYSTEM = "system"
    MOCHA = "mocha"
    LATTE = "latte"


def validate_url(url: str) -> str:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        typer.BadParameter: If URL format is invalid
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise typer.BadParameter(f"Invalid URL: {url}")
    return url


def resolve_theme(option: ThemeOption) -> ThemeName:
    """Convert ThemeOption to actual theme name.

    Args:
        option: Theme option from CLI

    Returns:
        "mocha" or "latte"
    """
    match option:
        case ThemeOption.SYSTEM:
            return detect_system_theme()
        case ThemeOption.MOCHA:
            return "mocha"
        case _:
            return "latte"


def resolve_binary(common: Path | None, specific: Path | None) -> Path | None:
    """Resolve binary path (specific > common > None).

    Args:
        common: Common binary path
        specific: Specific binary path

    Returns:
        Resolved binary path (specific takes priority, fallback to common)
    """
    return specific if specific is not None else common


def create_agent(
    agent_spec: str,
    sdk_options_json: str | None,
    binary_path: Path | None,
    opencode_url: str | None,
) -> Agent:
    """Create agent from agent spec.

    Args:
        agent_spec: "claude" | "claude:sonnet" | "opencode"
        sdk_options_json: JSON string (SDK options)
        binary_path: Binary path (auto-detect if None)
        opencode_url: OpenCode server URL (auto-start if None)

    Returns:
        Agent instance

    Raises:
        typer.BadParameter: If agent type is unknown or JSON is invalid
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
    """CLI mode main function (original logic).

    Args:
        execute_agent: Execute agent
        verify_agent: Verify agent (Optional)
        execute_prompt_spec: Execute prompt spec (uses built-in if None)
        verify_prompt_spec: Verify prompt spec (uses built-in if None)
        execute_extra: Additional execute prompt
        verify_extra: Additional verify prompt
        ui: UI Protocol implementation
        session_store: SessionStore instance
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
        time_parts.append(f"{hours} hour(s)")
    if minutes > 0:
        time_parts.append(f"{minutes} minute(s)")
    if secs > 0 or not time_parts:
        time_parts.append(f"{secs} second(s)")

    elapsed_str = " ".join(time_parts)
    await ui.show_status(f"✅ All tasks completed. (Elapsed time: {elapsed_str})")
    await ui.show_status("Press Ctrl+C to exit.")

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
    """TUI mode main function (parallel execution of TUI and ExecutionLoop).

    Args:
        execute_agent: Execute agent
        verify_agent: Verify agent (Optional)
        execute_prompt_spec: Execute prompt spec (uses built-in if None)
        verify_prompt_spec: Verify prompt spec (uses built-in if None)
        execute_extra: Additional execute prompt
        verify_extra: Additional verify prompt
        ui: UI Protocol implementation
        session_store: SessionStore instance
    """
    if not isinstance(ui, TUI):
        raise TypeError("ui must be TUI instance for TUI mode")

    async def monitor_shutdown(tg: anyio.abc.TaskGroup) -> None:
        """Monitor shutdown event (TUI → ExecutionLoop termination)."""
        await ui.shutdown_event.wait()
        tg.cancel_scope.cancel()

    async def run_execution_loop() -> None:
        """Run ExecutionLoop (after TUI is ready)."""

        start_time = time.time()

        try:
            # Wait for TUI readiness (10 second timeout)
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

            if isinstance(ui, TUI):
                ui.set_execution_loop(loop)

            await loop.run(
                execute_prompt=execute_prompt_spec,
                execute_extra=execute_extra,
                verify_prompt=verify_prompt_spec,
                verify_extra=verify_extra,
            )

            elapsed_seconds = time.time() - start_time
            ui.post_message(CompletionMessage("All tasks completed.", elapsed_seconds=elapsed_seconds))

            try:
                completion_event = anyio.Event()
                await completion_event.wait()
            except (KeyboardInterrupt, anyio.get_cancelled_exc_class()):
                pass
        except Exception as e:
            # Display error in UI and request shutdown
            try:
                await ui.show_status(f"[bold red]Error: {e}[/bold red]")
            except Exception:
                pass
            ui.post_message(ShutdownRequestMessage())
            raise  # Re-raise to cancel other tasks in TaskGroup

    try:
        async with anyio.create_task_group() as tg:
            # Start TUI (background)
            tg.start_soon(ui.run_async)
            # Start ExecutionLoop (after TUI ready)
            tg.start_soon(run_execution_loop)
            # Monitor shutdown (separate task)
            tg.start_soon(monitor_shutdown, tg)
    except* (SystemExit, KeyboardInterrupt):
        # Normal termination (Ctrl+C etc) - ExceptionGroup handling
        pass
    except* Exception as eg:
        for e in eg.exceptions:
            error_console.print("\n[bold red]═══ Unhandled Error ═══[/bold red]")
            error_console.print(f"[red]Type: {type(e).__name__}[/red]")
            error_console.print(f"[red]Message: {e}[/red]")
            error_console.print("\n[yellow]Traceback:[/yellow]")
            traceback.print_exception(type(e), e, e.__traceback__)
        raise typer.Exit(1)


@app.command(name="work")
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
    theme: ThemeOption = typer.Option(
        ThemeOption.SYSTEM,
        "--theme",
        help="TUI theme (system: auto-detect, mocha: dark, latte: light)",
        case_sensitive=False,
    ),
    log: Path | None = typer.Option(None, "--log", help="Log file path"),
) -> None:
    """Work with Sisyphus multi-agent system."""
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

    # DEBUG: Confirm verify_agent creation
    console.print(f"[yellow]DEBUG: verify_spec={verify_spec}, verify_agent={verify_agent}[/yellow]")

    resolved_theme = resolve_theme(theme)
    ui = create_ui("cli" if no_tui else "tui", theme=resolved_theme if not no_tui else None)

    session_store = SessionStore()

    try:
        if no_tui:
            # CLI mode (trio/asyncio auto-select - no backend specified)
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
            # TUI mode (Textual supports asyncio only)
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


@app.command(name="reset")
def reset(
    include_task_specs: bool = typer.Option(
        False, "--include-task-specs", help="Also delete ai-todolist.md and notepad.md"
    ),
) -> None:
    """Clean up generated files (sessions/, logs/, optionally docs)."""
    base_targets = [Path("sessions"), Path("logs")]
    doc_targets = [Path("ai-todolist.md"), Path("notepad.md")]
    targets = base_targets + (doc_targets if include_task_specs else [])

    for target in targets:
        try:
            if target.is_dir():
                shutil.rmtree(target)
                console.print(f"[green]✓[/green] Deleted directory: {target}")
            elif target.is_file():
                target.unlink()
                console.print(f"[green]✓[/green] Deleted file: {target}")
            else:
                console.print(f"[yellow]⊘[/yellow] Not found: {target}")
        except (PermissionError, OSError) as e:
            error_console.print(f"[red]✗[/red] Failed to delete {target}: {e}")

    console.print("\n[bold green]Reset complete![/bold green]")


if __name__ == "__main__":
    app()
