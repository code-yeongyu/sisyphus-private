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
from pydantic import ValidationError
from rich.console import Console
from ruamel.yaml import YAML, YAMLError

from sisyphus.agents.claude import ClaudeAgent
from sisyphus.agents.opencode import OpenCodeAgent
from sisyphus.core.loop import ExecutionLoop
from sisyphus.core.plan_linter import PlanLinter
from sisyphus.core.plan_loader import PlanLoader
from sisyphus.core.plan_navigator import PlanNavigator
from sisyphus.core.session import SessionStore
from sisyphus.core.tasks import TaskValidator
from sisyphus.ui.base import create_ui
from sisyphus.ui.tui.app import TUI, CompletionMessage, ShutdownRequestMessage
from sisyphus.utils.formatting import (
    OutputFormat,
    print_children,
    print_completion_report,
    print_overview,
    print_references,
    print_task,
    print_verification,
)
from sisyphus.utils.git import detect_base_branch, find_commits_with_files, generate_rebase_guide, is_on_main_branch
from sisyphus.utils.logging import LoggerFactory
from sisyphus.utils.plan_types import Todo, TodoStatus
from sisyphus.utils.theme import ThemeName, detect_system_theme

if TYPE_CHECKING:
    from sisyphus.agents.base import Agent
    from sisyphus.ui.base import UIProtocol

app = typer.Typer(name="sisyphus", help="Sisyphus Multi-Agent System")
console = Console()
error_console = Console(stderr=True)

# Sisyphus generated files patterns for .gitignore / .git/info/exclude
SISYPHUS_IGNORE_PATTERNS = [
    "# Sisyphus generated files",
    "ai-todolist.md",
    "notepad.md",
    "sessions/",
    "logs/",
    "agentloop.json",
    "claude_session_*.log",
]


def _is_duplicate_pattern(existing_content: str, pattern: str) -> bool:
    """Check if pattern already exists (exact match only).

    Args:
        existing_content: Full file content
        pattern: Pattern to check

    Returns:
        True if pattern exists, False otherwise
    """
    # Check exact line match (with or without trailing newline)
    lines = existing_content.splitlines()
    return pattern in lines or pattern.strip() in lines


def _add_patterns_to_file(file_path: Path, patterns: list[str]) -> list[str]:
    """Add patterns to file, return list of added patterns."""
    # Read existing content
    if file_path.exists():
        existing_content = file_path.read_text()
    else:
        existing_content = ""

    # Filter out duplicates
    new_patterns = [p for p in patterns if not _is_duplicate_pattern(existing_content, p)]

    if not new_patterns:
        return []

    # Append new patterns (with newline before if file doesn't end with one)
    content_to_add = ""
    if existing_content and not existing_content.endswith("\n"):
        content_to_add = "\n"
    content_to_add += "\n".join(new_patterns) + "\n"

    file_path.write_text(existing_content + content_to_add)
    return new_patterns


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
    cwd: Path | None = None,
) -> Agent:
    """Create agent from agent spec.

    Args:
        agent_spec: "claude" | "claude:sonnet" | "opencode"
        sdk_options_json: JSON string (SDK options)
        binary_path: Binary path (auto-detect if None)
        opencode_url: OpenCode server URL (auto-start if None)
        cwd: Working directory for Claude Agent SDK (auto-detect if None)

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
            working_dir = str(cwd) if cwd else str(Path.cwd())
            return cast("Agent", ClaudeAgent(model=model, sdk_options=sdk_options, cwd=working_dir))
        case "opencode":
            return cast("Agent", OpenCodeAgent(binary=binary_path, server_url=opencode_url))
        case _:
            raise typer.BadParameter(f"Unknown agent type: {agent_type}")


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
            # Wait for TUI readiness (10 second timeout)
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


@app.command(name="ignore")
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
            added_patterns = _add_patterns_to_file(target_file, SISYPHUS_IGNORE_PATTERNS)
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


@app.command(name="clean-history")
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


plan_app = typer.Typer(name="plan", help="Work plan management")
app.add_typer(plan_app)

execute_phase_app = typer.Typer(name="execute-phase", help="Execute phase commands")
app.add_typer(execute_phase_app)

verify_phase_app = typer.Typer(name="verify-phase", help="Verify phase commands")
app.add_typer(verify_phase_app)


@execute_phase_app.command(name="get-overview")
def get_overview(rich: bool = typer.Option(False, "--rich", help="Use Rich table format")) -> None:
    """Get execution overview (user_request, background, status, workflow, todos depth-1)."""
    try:
        loader = PlanLoader()
        plan = loader.load()

        print_overview(plan, format=OutputFormat.RICH if rich else OutputFormat.PLAIN)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@plan_app.command(name="get")
def get_plan_info(
    what: str = typer.Argument(..., help="What to get: task, reference"),
    current: bool = typer.Option(False, "--current", help="Get current task"),
    next_task: bool = typer.Option(False, "--next", help="Get next pending task"),
    task_id: str | None = typer.Option(None, "--id", help="Specific task ID"),
    show_references: bool = typer.Option(False, "--show-references", help="Show only references"),
    show_children: bool = typer.Option(False, "--show-children", help="Show only children"),
    show_verification: bool = typer.Option(False, "--show-verification", help="Show only verification spec"),
    show_all: bool = typer.Option(False, "--show-all", help="Show complete task info (default)"),
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format (default: plain text)"),
) -> None:
    """Get information from work plan."""
    output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN

    try:
        loader = PlanLoader()
        plan = loader.load()
        navigator = PlanNavigator(plan)

        match what:
            case "task":
                task = None
                if current:
                    task = navigator.get_current_task()
                    if task is None:
                        console.print("[yellow]작업이 시작되지 않았습니다[/yellow]")
                        raise typer.Exit(0)
                elif next_task:
                    task = navigator.get_next_task()
                    if task is None:
                        console.print("[green]모든 작업이 완료되었습니다![/green]")
                        raise typer.Exit(0)
                elif task_id:
                    task = navigator.find_todo_by_id(task_id)
                    if task is None:
                        console.print(f"[red]작업 ID를 찾을 수 없습니다: {task_id}[/red]")
                        raise typer.Exit(1)
                else:
                    console.print("[red]--current, --next, --id 중 하나를 선택하세요[/red]")
                    raise typer.Exit(1)

                if show_references:
                    refs = navigator.get_task_references(task.id)
                    print_references(refs, format=output_format)
                elif show_children:
                    children = navigator.get_task_children(task.id)
                    print_children(children, format=output_format)
                elif show_verification:
                    verifications = navigator.get_task_verification(task.id)
                    print_verification(verifications, format=output_format)
                else:
                    print_task(task, format=output_format)

            case "reference":
                console.print("[yellow]Reference lookup not yet implemented[/yellow]")
                raise typer.Exit(1)

            case _:
                console.print(f"[red]Unknown option: {what}[/red]")
                raise typer.Exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except ValidationError as e:
        console.print(f"[red]YAML 검증 실패:[/red]\n{e}")
        raise typer.Exit(1)


@plan_app.command(name="set")
def set_plan_info(
    what: str = typer.Argument(..., help="What to set: current-task, task-status"),
    value: str = typer.Argument(..., help="Value to set"),
    status: str | None = typer.Option(None, "--status", help="Task status (for task-status)"),
    recursive: bool = typer.Option(False, "--recursive", help="Apply to all children recursively"),
) -> None:
    """Update work plan information."""
    try:
        loader = PlanLoader()
        plan = loader.load()

        match what:
            case "current-task":
                plan.status.work_mode.current_task_id = value
                loader.save(plan)
                console.print(f"[green]✓[/green] Current task set to: {value}")

            case "task-status":
                if status is None:
                    console.print("[red]--status 옵션이 필요합니다[/red]")
                    raise typer.Exit(1)

                navigator = PlanNavigator(plan)
                task = navigator.find_todo_by_id(value)
                if task is None:
                    console.print(f"[red]작업 ID를 찾을 수 없습니다: {value}[/red]")
                    raise typer.Exit(1)

                # 재귀 옵션 처리
                task_ids_to_update: list[str | int]
                if recursive:
                    descendants = navigator.get_all_descendants(value)
                    task_ids_to_update = [value] + [d.id for d in descendants]
                else:
                    task_ids_to_update = [value]

                # 모든 task 업데이트 (Pydantic immutable → 새 객체 생성)
                updated_todos = _update_task_statuses(plan.todos, task_ids_to_update, status)
                plan = plan.model_copy(update={"todos": updated_todos})

                loader.save(plan)
                console.print(f"[green]✓[/green] {len(task_ids_to_update)}개 태스크 상태 변경: {status}")

            case _:
                console.print(f"[red]Unknown option: {what}[/red]")
                raise typer.Exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except ValidationError as e:
        console.print(f"[red]YAML 검증 실패:[/red]\n{e}")
        raise typer.Exit(1)


def _update_task_statuses(todos: list[Todo], task_ids: list[str | int], new_status: str) -> list[Todo]:
    """Recursively update task statuses (immutable).

    Args:
        todos: List of todos to update
        task_ids: IDs of tasks to update
        new_status: New status value

    Returns:
        Updated list of todos
    """
    result = []
    for todo in todos:
        if todo.id in task_ids:
            # 상태 변경
            updated = todo.model_copy(update={"status": TodoStatus(new_status)})
            # children도 재귀 업데이트
            if updated.children:
                updated = updated.model_copy(
                    update={"children": _update_task_statuses(updated.children, task_ids, new_status)}
                )
            result.append(updated)
        else:
            # children만 재귀 확인
            if todo.children:
                updated = todo.model_copy(
                    update={"children": _update_task_statuses(todo.children, task_ids, new_status)}
                )
                result.append(updated)
            else:
                result.append(todo)
    return result


@plan_app.command(name="set-verification")
def set_verification_status(
    task_id: str = typer.Argument(..., help="Task ID"),
    verify_id: str = typer.Argument(..., help="Verification item ID"),
    completed: bool = typer.Option(True, "--completed/--not-completed", help="Mark as completed"),
) -> None:
    """Mark a verification item as completed."""
    try:
        loader = PlanLoader()
        plan = loader.load()
        navigator = PlanNavigator(plan)

        # Task 찾기
        task = navigator.find_todo_by_id(task_id)
        if task is None:
            console.print(f"[red]작업 ID를 찾을 수 없습니다: {task_id}[/red]")
            raise typer.Exit(1)

        # Verification item 찾기
        verify_item = next((v for v in task.verification_spec if v.id == verify_id), None)
        if verify_item is None:
            console.print(f"[red]검증 ID를 찾을 수 없습니다: {verify_id}[/red]")
            raise typer.Exit(1)

        # 상태 업데이트 (immutable)
        updated_todos = _update_verification_status(plan.todos, task_id, verify_id, completed)
        plan = plan.model_copy(update={"todos": updated_todos})

        loader.save(plan)
        status_str = "완료" if completed else "미완료"
        console.print(f"[green]✓[/green] 검증 항목 {verify_id} → {status_str}")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except ValidationError as e:
        console.print(f"[red]YAML 검증 실패:[/red]\n{e}")
        raise typer.Exit(1)


def _update_verification_status(todos: list[Todo], task_id: str, verify_id: str, completed: bool) -> list[Todo]:
    """Recursively update verification item status (immutable).

    Args:
        todos: List of todos to search
        task_id: Target task ID
        verify_id: Verification item ID to update
        completed: Completion status

    Returns:
        Updated list of todos
    """
    result = []
    for todo in todos:
        if todo.id == task_id:
            # 해당 task의 verification_spec 업데이트
            updated_specs = [
                v.model_copy(update={"completed": completed}) if v.id == verify_id else v
                for v in todo.verification_spec
            ]
            updated = todo.model_copy(update={"verification_spec": updated_specs})
            result.append(updated)
        else:
            # children 재귀 확인
            if todo.children:
                updated = todo.model_copy(
                    update={"children": _update_verification_status(todo.children, task_id, verify_id, completed)}
                )
                result.append(updated)
            else:
                result.append(todo)
    return result


@plan_app.command(name="check")
def check_completion(
    task_id: str = typer.Argument(..., help="Task ID to check"),
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format (default: plain text)"),
) -> None:
    """Check if task can be marked as completed (checks children + verifications)."""
    output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN

    try:
        loader = PlanLoader()
        plan = loader.load()
        navigator = PlanNavigator(plan)

        report = navigator.check_task_completion(task_id)
        print_completion_report(report, format=output_format)

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@plan_app.command(name="lint")
def lint_plan(
    file_path: Path = typer.Option(
        Path("./ai-todolist.yaml"),
        "--file",
        "-f",
        help="YAML file path to lint",
    ),
) -> None:
    """Lint work plan YAML for schema validation."""
    try:
        yaml = YAML()
        yaml.preserve_quotes = True

        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            raise typer.Exit(1)

        with file_path.open("r", encoding="utf-8") as f:
            yaml_data = yaml.load(f)

        linter = PlanLinter({})
        errors = linter.lint(yaml_data)

        if errors:
            console.print(f"[red]✗ Validation failed: {len(errors)} error(s)[/red]\n")
            for error in errors:
                console.print(f"  [red]•[/red] {linter.format_error(error)}")
            raise typer.Exit(1)
        else:
            console.print("[green]✓ YAML validation passed. 0 errors.[/green]")

    except YAMLError as e:
        console.print(f"[red]YAML parsing error:[/red]\n{e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
