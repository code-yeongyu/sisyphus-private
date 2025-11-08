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
from sisyphus.core.plan_linter import LintError, PlanLinter
from sisyphus.core.plans.loader import load_plan
from sisyphus.core.plans.models import TodoStatus
from sisyphus.core.session import SessionStore
from sisyphus.core.status.manager import StatusManager
from sisyphus.core.task_validator import YamlTaskValidator
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
    ".sisyphus/",
    "notepad.md",
    "sessions/",
    "logs/",
    "agentloop.json",
    "claude_session_*.log",
]


async def _validate_plan(plan_path: Path, ui: UIProtocol) -> None:
    """Validate YAML plan with PlanLinter (순환참조, 의존성 완료 체크).

    Scope: 단일 YAML 파일 내부 work_plans 간 검증

    Args:
        plan_path: Path to YAML plan file
        ui: UI Protocol implementation

    Raises:
        ValueError: If validation fails
    """

    # YAML 파싱 (async)
    try:
        plan_doc = await load_plan(plan_path)
    except Exception as e:
        await ui.show_status(f"[red]Failed to load plan: {e}[/red]")
        raise ValueError(f"Plan load failed: {plan_path}") from e

    linter = PlanLinter(schema_doc={})
    errors = linter.validate_all(plan_doc, plan_path)

    if errors:
        by_category: dict[str, list[LintError]] = {}
        for error in errors:
            by_category.setdefault(error.category, []).append(error)

        error_msg = "[bold red]Plan validation failed:[/bold red]\n\n"
        for category, cat_errors in by_category.items():
            error_msg += f"[yellow]{category.upper()} ERRORS:[/yellow]\n"
            for err in cat_errors:
                error_msg += f"  - {linter.format_error(err)}\n"

        await ui.show_status(error_msg + "\nFix: Address all errors before running 'sisyphus work'.")
        raise ValueError(f"Validation failed: {len(errors)} errors")

    # 의존성 완료 여부 체크 (단일 PlanDocument 내부만)
    plans_map = {plan.id: plan for plan in plan_doc.work_plans}

    for plan in plan_doc.work_plans:
        for dep_id in plan.depends_on:
            # 같은 파일 내부의 의존 플랜만 체크
            if dep_id in plans_map:
                dep_plan = plans_map[dep_id]
                # 모든 todos가 completed인지 체크
                all_completed = all(t.status == TodoStatus.completed for t in dep_plan.todos)
                if not all_completed:
                    incomplete_count = sum(1 for t in dep_plan.todos if t.status != TodoStatus.completed)
                    await ui.show_status(
                        f"[red]Dependency not completed:[/red]\n\n"
                        f"  Plan '{plan.id}' depends on '{dep_id}', "
                        f"but '{dep_id}' has {incomplete_count} incomplete todo(s).\n\n"
                        + "Fix: Complete all todos in dependent plans first."
                    )
                    raise ValueError(f"Dependency '{dep_id}' not completed")


async def _detect_plan_path(ui: UIProtocol) -> Path | None:
    """Detect YAML plan file with improved UX.

    Priority:
    1. Auto-select if .sisyphus/tasks/**/*.yaml == 1 file (재귀 탐색)
    2. Error if multiple YAML files (need manual selection)

    Args:
        ui: UI Protocol implementation

    Returns:
        Path to YAML file or None

    Raises:
        ValueError: If multiple plans found
    """

    # 0. 워크트리 루트 먼저 감지 (모든 경로 체크의 기준점)
    worktree_root = await StatusManager.detect_worktree()

    # 1. Markdown 에러 (워크트리 기준으로 체크)
    # 1. YAML 파일 재귀 탐색 (워크트리 기준 경로)
    tasks_dir = worktree_root / ".sisyphus" / "tasks"

    if not tasks_dir.exists():
        await ui.show_status(
            "[yellow]No '.sisyphus/tasks/' directory found.[/yellow]\n\n"
            "Create v3.0 YAML plan:\n"
            "  mkdir -p .sisyphus/tasks\n"
            "  vi .sisyphus/tasks/my-plan.yaml"
        )
        return None

    # 재귀 탐색 + 대소문자 무시 (glob은 대소문자 구분하므로 양쪽 다 검색)
    yaml_files = []
    for pattern in ("**/*.yaml", "**/*.yml", "**/*.YAML", "**/*.YML"):
        yaml_files.extend(tasks_dir.glob(pattern))
    # 중복 제거 (같은 파일이 여러 패턴에 매칭될 수 있음)
    yaml_files = list(set(yaml_files))

    if len(yaml_files) == 0:
        await ui.show_status(
            "[yellow]No YAML plans in '.sisyphus/tasks/'.[/yellow]\n\n"
            "Create v3.0 YAML plan:\n"
            "  vi .sisyphus/tasks/my-plan.yaml"
        )
        return None
    elif len(yaml_files) == 1:
        return yaml_files[0].absolute()
    else:
        # 다중 YAML: 사용자 선택 입력 (사용자 요청 반영)
        rel_paths = [f.relative_to(worktree_root) for f in yaml_files]

        # CLI 모드: typer.prompt 사용 가능
        # TUI 모드: ui.get_input() 사용 (UIProtocol 메서드)
        await ui.show_status(
            f"[yellow]Multiple YAML plans found ({len(yaml_files)} files).[/yellow]\n\nAvailable plans:"
        )

        for idx, path in enumerate(rel_paths, start=1):
            await ui.show_status(f"  {idx}. {path}")

        # 입력 받기 (TUI: get_input returns queued input, CLI: typer.prompt with anyio wrapper)
        # UIProtocol.get_input() signature: async def get_input(self) -> str | None (NO parameters)

        # TUI 모드: show_status로 프롬프트 표시 후 get_input() 호출
        if isinstance(ui, TUI):
            await ui.show_status(f"\n[yellow]Enter selection (1-{len(yaml_files)}):[/yellow]")
            selection = await ui.get_input()
            if selection is None:
                raise ValueError("User cancelled selection")
        else:
            # CLI 모드: anyio.to_thread.run_sync로 typer.prompt 래핑 (이벤트 루프 블로킹 방지)
            selection = str(
                await anyio.to_thread.run_sync(  # pyright: ignore[reportAttributeAccessIssue]
                    lambda: typer.prompt(f"Select plan (1-{len(yaml_files)})", default=1, type=int)
                )
            )

        try:
            idx = int(selection) - 1
            if idx < 0 or idx >= len(yaml_files):
                raise ValueError("Index out of range")
            return yaml_files[idx].absolute()
        except (ValueError, IndexError) as e:
            await ui.show_status(f"[red]Invalid selection: {selection}[/red]")
            raise ValueError(f"Invalid plan selection: {selection}") from e


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

    plan_path = await _detect_plan_path(ui)
    if plan_path:
        await _validate_plan(plan_path, ui)

    task_validator = YamlTaskValidator(plan_path) if plan_path else None

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

    async def monitor_shutdown(tg: anyio.abc.TaskGroup) -> None:  # pyright: ignore[reportAttributeAccessIssue]
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
            plan_path = await _detect_plan_path(ui)
            if plan_path:
                await _validate_plan(plan_path, ui)

            task_validator = YamlTaskValidator(plan_path) if plan_path else None

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
        "notepad.md",
        ".sisyphus/",
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
