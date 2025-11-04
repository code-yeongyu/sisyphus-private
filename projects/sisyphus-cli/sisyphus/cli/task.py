from __future__ import annotations

import subprocess
from datetime import UTC, datetime

import typer
from rich.console import Console

from sisyphus.cli.common import resolve_cwd
from sisyphus.core.plan_loader import PlanLoader
from sisyphus.core.plan_navigator import PlanNavigator
from sisyphus.utils.formatting import OutputFormat, print_task
from sisyphus.utils.plan_types import Todo, TodoStatus

task_app = typer.Typer(name="task", help="Task execution commands")
console = Console()

verify_app = typer.Typer(name="verify", help="Verification commands")
task_app.add_typer(verify_app)


@task_app.command(name="show")
def show_task(
    task_id: str = typer.Argument(..., help="Task ID to display"),
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        task = navigator.find_todo_by_id(task_id)
        if task is None:
            console.print(f"[red]작업 ID를 찾을 수 없습니다: {task_id}[/red]")
            raise typer.Exit(1)

        output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
        print_task(task, format=output_format)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@task_app.command(name="current")
def show_current(
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        task = navigator.get_current_task()
        if task is None:
            console.print("[yellow]작업이 시작되지 않았습니다[/yellow]")
            raise typer.Exit(0)

        output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
        print_task(task, format=output_format)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@task_app.command(name="next")
def show_next(
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        task = navigator.get_next_task()
        if task is None:
            console.print("[green]모든 작업이 완료되었습니다![/green]")
            raise typer.Exit(0)

        output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
        print_task(task, format=output_format)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@task_app.command(name="previous")
def show_previous(
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        task = navigator.get_previous_task()
        if task is None:
            if plan.status.execution.started:
                console.print("[yellow]첫 작업입니다[/yellow]")
            else:
                console.print("[yellow]작업이 시작되지 않았습니다[/yellow]")
            raise typer.Exit(0)

        output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
        print_task(task, format=output_format)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@task_app.command(name="continue")
def continue_work(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    """Continue working on current or next task."""
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        if not plan.status.execution.started:
            first_task = navigator.get_next_task(current_id=None)
            if first_task is None:
                console.print("[red]작업이 없습니다[/red]")
                raise typer.Exit(1)

            plan.status.execution.started = True
            plan.status.execution.started_at = datetime.now(UTC).isoformat()
            plan.status.work_mode.current_task_id = str(first_task.id)

            first_task.status = TodoStatus.in_progress
            first_task.status_changed_at = datetime.now(UTC).isoformat()

            loader.save(plan)
            console.print(f"[green]작업을 시작합니다: {first_task.title}[/green]")
            return

        current_task_id = plan.status.work_mode.current_task_id
        if current_task_id is None:
            console.print("[red]현재 작업 ID가 없습니다[/red]")
            raise typer.Exit(1)

        report = navigator.check_task_completion(current_task_id)

        if not report.can_complete:
            console.print("[yellow]다음 작업으로 넘어갈 수 없습니다[/yellow]")

            if not report.all_children_completed:
                descendants = navigator.get_all_descendants(current_task_id)
                console.print(f"자식 작업: {report.children_summary['completed']}/{len(descendants)} 완료")

            if not report.all_verifications_completed:
                console.print(
                    f"검증: {report.verification_summary['completed']}/{report.verification_summary['total']} 완료"
                )

            raise typer.Exit(1)

        current_task = navigator.find_todo_by_id(current_task_id)
        if current_task is None:
            console.print("[red]현재 작업을 찾을 수 없습니다[/red]")
            raise typer.Exit(1)

        current_task.status = TodoStatus.completed
        current_task.status_changed_at = datetime.now(UTC).isoformat()

        next_task = navigator.get_next_task(current_task_id)
        if next_task is None:
            plan.status.execution.completed = True
            plan.status.execution.completed_at = datetime.now(UTC).isoformat()
            plan.status.work_mode.current_task_id = None
            loader.save(plan)
            console.print("[green]모든 작업이 완료되었습니다![/green]")
            return

        next_task.status = TodoStatus.in_progress
        next_task.status_changed_at = datetime.now(UTC).isoformat()
        plan.status.work_mode.current_task_id = str(next_task.id)

        loader.save(plan)
        console.print(f"[green]다음 작업으로 이동: {next_task.title}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@verify_app.command(name="bash")
def verify_bash(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
    evidence: str | None = typer.Option(None, "--evidence", help="Additional verification evidence"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        result = navigator.next_unverified()
        if result is None:
            console.print("[green]✓ 모든 검증이 완료되었습니다![/green]")
            raise typer.Exit(0)

        verify_item, current_idx, total_count = result

        console.print(f"\n[bold cyan]━━━ 검증 {current_idx}/{total_count} ━━━[/bold cyan]")
        console.print(f"[bold]제목:[/bold] {verify_item.title}")
        console.print(f"[bold]설명:[/bold] {verify_item.description}\n")

        if not verify_item.bash:
            console.print("[yellow]bash 검증이 없습니다[/yellow]")
            raise typer.Exit(0)

        all_passed = True
        for bash_spec in verify_item.bash:
            console.print(f"[bold]명령어:[/bold] {bash_spec.execute}")
            console.print("실행 중...")

            result_proc = subprocess.run(bash_spec.execute, check=False, shell=True, capture_output=True, text=True)

            if result_proc.returncode == bash_spec.expected_exit_code:
                console.print(f"[green]✓ 성공[/green] (exit_code={result_proc.returncode})")

                now = datetime.now(UTC).isoformat()

                def update_verification(todos: list[Todo]) -> list[Todo]:
                    updated: list[Todo] = []
                    for todo in todos:
                        updated_specs = [
                            (
                                v.model_copy(
                                    update={
                                        "verified": True,
                                        "verified_at": now,
                                        "verification_evidence": f"Command succeeded: {bash_spec.execute}"
                                        + (f"\nAdditional: {evidence}" if evidence else ""),
                                    }
                                )
                                if v.id == verify_item.id
                                else v
                            )
                            for v in todo.verification_spec
                        ]
                        updated_todo = todo.model_copy(update={"verification_spec": updated_specs})
                        if todo.children:
                            updated_todo = updated_todo.model_copy(
                                update={"children": update_verification(todo.children)}
                            )
                        updated.append(updated_todo)
                    return updated

                plan = plan.model_copy(update={"todos": update_verification(plan.todos)})
                loader.save(plan)
            else:
                all_passed = False
                console.print(f"[red]✗ 실패[/red] (exit_code={result_proc.returncode})")
                console.print(f"  예상 exit code: {bash_spec.expected_exit_code}")
                if result_proc.stderr:
                    console.print(f"  stderr: {result_proc.stderr}")

        if evidence and all_passed:
            console.print(f"\n[bold]증거 기록됨:[/bold] {evidence}")

        if all_passed:
            console.print("\n[green]다음 검증으로 이동합니다...[/green]")
        else:
            console.print("\n[red]일부 검증이 실패했습니다[/red]")
            raise typer.Exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@verify_app.command(name="llm")
def verify_llm(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        result = navigator.next_unverified()
        if result is None:
            console.print("[green]✓ 모든 검증이 완료되었습니다![/green]")
            raise typer.Exit(0)

        verify_item, current_idx, total_count = result

        console.print(f"\n[bold cyan]━━━ 검증 {current_idx}/{total_count} ━━━[/bold cyan]")
        console.print(f"[bold]제목:[/bold] {verify_item.title}")
        console.print(f"[bold]설명:[/bold] {verify_item.description}\n")

        if not verify_item.llm_judge:
            console.print("[yellow]LLM 검증이 없습니다[/yellow]")
            raise typer.Exit(0)

        for llm_spec in verify_item.llm_judge:
            console.print(f"[bold]판단 주체:[/bold] {llm_spec.by}")
            console.print(f"[bold]지시사항:[/bold] {llm_spec.instruction}\n")

            if llm_spec.context_commands:
                console.print("[bold]컨텍스트 명령어:[/bold]")
                for cmd in llm_spec.context_commands:
                    console.print(f"  - {cmd}")
                console.print()

        console.print("[yellow]LLM 검증을 수행한 후 'task verify llm mark' 명령어로 완료 표시하세요[/yellow]")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@verify_app.command(name="llm-mark")
def verify_llm_mark(
    verify_id: str = typer.Argument(..., help="Verification item ID"),
    evidence: str = typer.Option(..., "--evidence", help="Verification evidence"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()

        now = datetime.now(UTC).isoformat()

        def update_verification(todos: list[Todo]) -> list[Todo]:
            updated: list[Todo] = []
            for todo in todos:
                updated_specs = [
                    (
                        v.model_copy(update={"verified": True, "verified_at": now, "verification_evidence": evidence})
                        if v.id == verify_id
                        else v
                    )
                    for v in todo.verification_spec
                ]
                updated_todo = todo.model_copy(update={"verification_spec": updated_specs})
                if todo.children:
                    updated_todo = updated_todo.model_copy(update={"children": update_verification(todo.children)})
                updated.append(updated_todo)
            return updated

        plan = plan.model_copy(update={"todos": update_verification(plan.todos)})
        loader.save(plan)

        console.print(f"[green]✓ LLM 검증이 완료 표시되었습니다: {verify_id}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@verify_app.command(name="manual")
def verify_manual(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        result = navigator.next_unverified()
        if result is None:
            console.print("[green]✓ 모든 검증이 완료되었습니다![/green]")
            raise typer.Exit(0)

        verify_item, current_idx, total_count = result

        console.print(f"\n[bold cyan]━━━ 검증 {current_idx}/{total_count} ━━━[/bold cyan]")
        console.print(f"[bold]제목:[/bold] {verify_item.title}")
        console.print(f"[bold]설명:[/bold] {verify_item.description}\n")

        console.print("[yellow]수동 검증을 수행한 후 'task verify manual mark' 명령어로 완료 표시하세요[/yellow]")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@verify_app.command(name="manual-mark")
def verify_manual_mark(
    verify_id: str = typer.Argument(..., help="Verification item ID"),
    evidence: str = typer.Option(..., "--evidence", help="Manual verification evidence"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()

        now = datetime.now(UTC).isoformat()

        def update_verification(todos: list[Todo]) -> list[Todo]:
            updated: list[Todo] = []
            for todo in todos:
                updated_specs = [
                    (
                        v.model_copy(
                            update={
                                "orchestrator_manually_verified": True,
                                "manual_verification_evidence": evidence,
                                "verified": True,
                                "verified_at": now,
                            }
                        )
                        if v.id == verify_id
                        else v
                    )
                    for v in todo.verification_spec
                ]
                updated_todo = todo.model_copy(update={"verification_spec": updated_specs})
                if todo.children:
                    updated_todo = updated_todo.model_copy(update={"children": update_verification(todo.children)})
                updated.append(updated_todo)
            return updated

        plan = plan.model_copy(update={"todos": update_verification(plan.todos)})
        loader.save(plan)

        console.print(f"[green]✓ 수동 검증이 완료 표시되었습니다: {verify_id}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@verify_app.command(name="status")
def verify_status(
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        PlanNavigator(plan)

        all_verifications: list[tuple[str, str, bool]] = []

        def collect_verifications(todos: list[Todo]) -> None:
            for todo in todos:
                for verify_item in todo.verification_spec:
                    all_verifications.append((verify_item.id, verify_item.title, verify_item.verified))
                if todo.children:
                    collect_verifications(todo.children)

        collect_verifications(plan.todos)

        if not all_verifications:
            console.print("[yellow]검증 항목이 없습니다[/yellow]")
            raise typer.Exit(0)

        verified_count = sum(1 for _, _, verified in all_verifications if verified)
        total_count = len(all_verifications)

        console.print(f"\n[bold]검증 상태:[/bold] {verified_count}/{total_count} 완료\n")

        for verify_id, title, verified in all_verifications:
            status_icon = "[green]✓[/green]" if verified else "[yellow]○[/yellow]"
            console.print(f"{status_icon} [{verify_id}] {title}")

        console.print()
        if verified_count == total_count:
            console.print("[green]✓ 모든 검증이 완료되었습니다![/green]")
        else:
            console.print(f"[yellow]남은 검증: {total_count - verified_count}개[/yellow]")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
