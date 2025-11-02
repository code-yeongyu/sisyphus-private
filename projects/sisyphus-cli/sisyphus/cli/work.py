"""Work, ignore, and clean-history commands."""

from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import typer
from rich.console import Console

from sisyphus.core.loop import ExecutionLoop
from sisyphus.core.session import SessionStore
from sisyphus.core.tasks import TaskValidator
from sisyphus.ui.base import create_ui
from sisyphus.ui.tui.app import TUI, CompletionMessage, ShutdownRequestMessage
from sisyphus.utils.cli_helpers import ThemeOption, create_agent, resolve_binary, resolve_theme, validate_url
from sisyphus.utils.git import detect_base_branch, find_commits_with_files, generate_rebase_guide, is_on_main_branch
from sisyphus.utils.ignore import add_patterns_to_file
from sisyphus.utils.logging import LoggerFactory

if TYPE_CHECKING:
    from sisyphus.agents.base import Agent
    from sisyphus.ui.base import UIProtocol

work_app = typer.Typer(name="work", help="Work commands", no_args_is_help=False)
console = Console()
error_console = Console(stderr=True)

SISYPHUS_IGNORE_PATTERNS = [
    "# Sisyphus generated files",
    "ai-todolist.md",
    "notepad.md",
    "sessions/",
    "logs/",
    "agentloop.json",
    "claude_session_*.log",
]


async def _main_cli(
    execute_agent: Agent,
    verify_agent: Agent | None,
    execute_extra: str | None,
    verify_extra: str | None,
    ui: UIProtocol,
    session_store: SessionStore,
) -> None:
    """CLI mode main function (original logic).

    Args:
        execute_agent: Execute agent
        verify_agent: Verify agent (Optional)
        execute_extra: Additional execute prompt
        verify_extra: Additional verify prompt
        ui: UI Protocol implementation
        session_store: SessionStore instance
    """
    start_time = time.time()

    logger_factory = LoggerFactory()

    task_validator = TaskValidator() if Path("ai-todolist.md").exists() else None

    loop = ExecutionLoop(
        execute_agent=execute_agent,
        ui=ui,
        session_store=session_store,
        logger_factory=logger_factory,
        verify_agent=verify_agent,
        task_validator=task_validator,
    )

    await loop.run(
        execute_extra=execute_extra,
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


async def _main_tui(
    execute_agent: Agent,
    verify_agent: Agent | None,
    execute_extra: str | None,
    verify_extra: str | None,
    ui: UIProtocol,
    session_store: SessionStore,
) -> None:
    """TUI mode main function (parallel execution of TUI and ExecutionLoop).

    Args:
        execute_agent: Execute agent
        verify_agent: Verify agent (Optional)
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
            with anyio.move_on_after(10.0) as cancel_scope:
                await ui.ready_event.wait()

            if cancel_scope.cancelled_caught:
                raise TimeoutError("TUI initialization timeout")

            logger_factory = LoggerFactory()
            task_validator = TaskValidator() if Path("ai-todolist.md").exists() else None

            if isinstance(ui, TUI):
                ui.set_task_validator(task_validator)

            loop = ExecutionLoop(
                execute_agent=execute_agent,
                ui=ui,
                session_store=session_store,
                logger_factory=logger_factory,
                verify_agent=verify_agent,
                task_validator=task_validator,
            )

            if isinstance(ui, TUI):
                ui.set_execution_loop(loop)

            await loop.run(
                execute_extra=execute_extra,
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
            try:
                await ui.show_status(f"[bold red]Error: {e}[/bold red]")
            except Exception:
                pass
            ui.post_message(ShutdownRequestMessage())
            raise

    try:
        async with anyio.create_task_group() as tg:
            tg.start_soon(ui.run_async)
            tg.start_soon(run_execution_loop)
            tg.start_soon(monitor_shutdown, tg)
    except* (SystemExit, KeyboardInterrupt):
        pass
    except* Exception as eg:
        for e in eg.exceptions:
            error_console.print("\n[bold red]═══ Unhandled Error ═══[/bold red]")
            error_console.print(f"[red]Type: {type(e).__name__}[/red]")
            error_console.print(f"[red]Message: {e}[/red]")
            error_console.print("\n[yellow]Traceback:[/yellow]")
            traceback.print_exception(type(e), e, e.__traceback__)
        raise typer.Exit(1)


@work_app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent type (claude|opencode)"),
    execute: str | None = typer.Option(None, "--execute", help="Execute agent (AGENT[:MODEL])"),
    verify: str | None = typer.Option(None, "--verify", help="Verify agent (AGENT[:MODEL])"),
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
    if ctx.invoked_subcommand is not None:
        return

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

    resolved_theme = resolve_theme(theme)
    ui = create_ui("cli" if no_tui else "tui", theme=resolved_theme if not no_tui else None)

    session_store = SessionStore()

    try:
        if no_tui:
            anyio.run(
                _main_cli,
                execute_agent,
                verify_agent,
                execute_extra_prompt,
                verify_extra_prompt,
                ui,
                session_store,
            )
        else:
            anyio.run(
                _main_tui,
                execute_agent,
                verify_agent,
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


@work_app.command(name="ignore")
def ignore(
    exclude_only: bool = typer.Option(False, "--exclude-only", help="Add only to .git/info/exclude (local)"),
    both: bool = typer.Option(False, "--both", help="Add to both .gitignore and .git/info/exclude"),
) -> None:
    """Add Sisyphus-generated files to git ignore configuration."""
    if exclude_only and both:
        error_console.print("[red]Error: Cannot use both --exclude-only and --both flags[/red]")
        raise typer.Exit(1)

    git_dir = Path(".git")
    if not git_dir.exists():
        error_console.print("[red]Error: Not in a git repository (.git directory not found)[/red]")
        raise typer.Exit(1)

    target_files: list[Path] = []
    if exclude_only:
        exclude_path = git_dir / "info" / "exclude"
        target_files.append(exclude_path)
    elif both:
        target_files.append(Path(".gitignore"))
        exclude_path = git_dir / "info" / "exclude"
        target_files.append(exclude_path)
    else:
        target_files.append(Path(".gitignore"))

    all_added: dict[str, list[str]] = {}

    for target_file in target_files:
        if target_file.name == "exclude":
            exclude_dir = target_file.parent
            if not exclude_dir.exists():
                try:
                    exclude_dir.mkdir(parents=True, exist_ok=True)
                except (PermissionError, OSError) as e:
                    error_console.print(f"[red]Error: Failed to create {exclude_dir}: {e}[/red]")
                    raise typer.Exit(1)

        try:
            added_patterns = add_patterns_to_file(target_file, SISYPHUS_IGNORE_PATTERNS)
            all_added[str(target_file)] = added_patterns
        except (PermissionError, OSError) as e:
            error_console.print(f"[red]Error: Failed to write to {target_file}: {e}[/red]")
            raise typer.Exit(1)

    total_added = sum(len(patterns) for patterns in all_added.values())

    if total_added == 0:
        console.print("[yellow]ℹ[/yellow] All Sisyphus patterns already present")
        console.print("[dim]No changes made[/dim]")
    else:
        for target_file, added_patterns in all_added.items():
            if added_patterns:
                console.print(f"[green]✓[/green] Added to {target_file}:")
                for pattern in added_patterns:
                    if pattern.startswith("#"):
                        console.print(f"  [dim]{pattern}[/dim]")
                    else:
                        console.print(f"  • {pattern}")
        console.print("\n[bold green]Successfully configured git to ignore Sisyphus files![/bold green]")


@work_app.command(name="clean-history")
def clean_history(
    base_branch: str | None = typer.Option(None, "--base-branch", help="Base branch (auto-detect if not specified)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without making changes"),
) -> None:
    """Remove Sisyphus-generated files from git history (current branch only)."""
    if is_on_main_branch():
        error_console.print("[red]Error: Cannot clean history on main/master branch[/red]")
        error_console.print("[yellow]Please switch to a feature branch first[/yellow]")
        raise typer.Exit(1)

    detected_base = detect_base_branch()
    if base_branch is None:
        base_branch = detected_base

    if base_branch is None:
        error_console.print("[red]Error: No base branch found[/red]")
        error_console.print("[yellow]Tried: origin/main, origin/master, origin/develop[/yellow]")
        error_console.print("[yellow]Specify one with --base-branch flag[/yellow]")
        raise typer.Exit(1)

    file_patterns = [
        "ai-todolist.md",
        "notepad.md",
        "sessions/",
        "logs/",
        "agentloop.json",
        "claude_session_*.log",
    ]

    commits = find_commits_with_files(base_branch, file_patterns)

    if not commits:
        console.print("[green]✓[/green] No commits containing Sisyphus files found")
        console.print(f"[dim]Git history is clean since {base_branch}[/dim]")
        return

    console.print("\n[bold yellow]⚠ Warning: Git History Modification[/bold yellow]")
    console.print(f"Found [bold]{len(commits)}[/bold] commit(s) with Sisyphus files since [cyan]{base_branch}[/cyan]")
    console.print("[yellow]This operation will rewrite git history.[/yellow]")
    console.print("[yellow]If these commits are already pushed, you'll need force-push.[/yellow]\n")

    if not dry_run:
        if not typer.confirm("Do you want to proceed?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            raise typer.Exit(0)

    guide = generate_rebase_guide(commits, base_branch)
    console.print(guide)

    if dry_run:
        console.print("\n[dim]DRY RUN - no changes made[/dim]")
