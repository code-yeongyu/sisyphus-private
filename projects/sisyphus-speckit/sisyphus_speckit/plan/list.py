"""Plan list display command."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import anyio
import typer
from rich.console import Console
from rich.table import Table
from sisyphus_core.core.plans.loader import load_plan
from sisyphus_core.utils.common import resolve_cwd

console = Console()


class PlanInfo(TypedDict):
    """Plan information dictionary."""

    id: str
    name: str
    filepath: str
    depends_on: list[str]
    created_at: str
    fully_done: bool
    dependency_count: int
    status: str


async def _get_current_plan_id(working_dir: Path) -> str | None:
    """Get current plan ID from status.json.

    Args:
        working_dir: Working directory path

    Returns:
        Current plan ID if available, None otherwise
    """
    status_path = working_dir / ".sisyphus" / "status.json"

    if not status_path.exists():
        return None

    try:
        status_content = await anyio.to_thread.run_sync(status_path.read_text)
        status_data = json.loads(status_content)  # pyright: ignore[reportUnknownArgumentType]
        if status_data.get("current_plan") and status_data["current_plan"].get("plan_path"):
            plan_path = status_data["current_plan"]["plan_path"]
            plan_name = Path(plan_path).stem
            return plan_name
    except Exception:
        pass

    return None


async def _check_dependencies_satisfied(
    plan_id: str, depends_on: list[str], _working_dir: Path, all_plans: dict[str, PlanInfo]  # pyright: ignore[reportUnusedParameter]
) -> bool:
    """Check if all dependencies are satisfied.

    Args:
        plan_id: Plan ID to check
        depends_on: List of dependency plan IDs
        working_dir: Working directory path
        all_plans: Dict of all plans with their data

    Returns:
        True if all dependencies are satisfied or no dependencies, False otherwise
    """
    if not depends_on:
        return True

    for dep_id in depends_on:
        if dep_id not in all_plans:
            return False
        dep_plan = all_plans[dep_id]
        if not dep_plan.get("fully_done"):
            return False

    return True


async def _calculate_status(
    plan_id: str,
    depends_on: list[str],
    fully_done: bool,
    current_plan_id: str | None,
    all_plans: dict[str, PlanInfo],
) -> str:
    """Calculate status for a plan.

    Args:
        plan_id: Plan ID
        depends_on: List of dependency plan IDs
        fully_done: Whether plan is fully done
        current_plan_id: Current plan ID from status.json
        all_plans: Dict of all plans with their data

    Returns:
        Status string: "작업중", "작업 가능", "완료됨"
    """
    if plan_id == current_plan_id:
        return "작업중"

    if fully_done:
        return "완료됨"

    dependencies_ok = await _check_dependencies_satisfied(plan_id, depends_on, Path.cwd(), all_plans)
    if dependencies_ok:
        return "작업 가능"

    return "의존성 대기중"


def _get_sort_key(plan_data: PlanInfo, status_order: dict[str, int]) -> tuple[int, str]:
    """Get sort key for a plan.

    Args:
        plan_data: Plan data dict
        status_order: Dict mapping status to sort order

    Returns:
        Tuple for sorting: (status_order, created_at)
    """
    status = plan_data["status"]
    created_at = plan_data["created_at"]
    return (status_order.get(status, 999), created_at)


def list_plans(
    directory: Path = typer.Option(Path(".sisyphus/tasks"), "--dir", "-d", help="Plan directory"),  # pyright: ignore[reportCallInDefaultInitializer]
    filter_status: str | None = typer.Option(None, "--filter", help="Filter by status"),  # pyright: ignore[reportCallInDefaultInitializer]
    sort_by: str = typer.Option("default", "--sort", help="Sort order (default/name/created)"),  # pyright: ignore[reportCallInDefaultInitializer]
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),  # pyright: ignore[reportCallInDefaultInitializer]
) -> None:
    """List all plans in a directory with their metadata.

    Displays plans in a formatted table showing name, file path, status, dependencies, and creation date.
    """

    async def _list_plans_async() -> None:
        working_dir = resolve_cwd(cwd)

        if not directory.is_absolute():
            plan_dir = working_dir / directory
        else:
            plan_dir = directory

        if not plan_dir.exists():
            console.print(f"[red]Error:[/red] Directory not found: {plan_dir}")
            raise typer.Exit(code=1)

        yaml_files = list(plan_dir.glob("*.yaml")) + list(plan_dir.glob("*.yml"))

        if not yaml_files:
            console.print(f"[yellow]No plans found in {plan_dir}[/yellow]")
            return

        plans_data: list[PlanInfo] = []
        all_plans_dict: dict[str, PlanInfo] = {}

        for yaml_file in yaml_files:
            try:
                plan_doc = await load_plan(yaml_file)

                for work_plan in plan_doc.work_plans:
                    fully_done = work_plan.execution.fully_done_at is not None
                    plan_info: PlanInfo = {
                        "id": work_plan.id,
                        "name": work_plan.name,
                        "filepath": str(yaml_file.relative_to(working_dir)),
                        "depends_on": work_plan.depends_on,
                        "created_at": work_plan.user_request.created_at,
                        "fully_done": fully_done,
                        "dependency_count": len(work_plan.depends_on),
                        "status": "",
                    }
                    all_plans_dict[work_plan.id] = plan_info
                    plans_data.append(plan_info)

            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Failed to load {yaml_file}: {e}")
                continue

        current_plan_id = await _get_current_plan_id(working_dir)

        for plan_info in plans_data:
            status = await _calculate_status(
                plan_info["id"],
                plan_info["depends_on"],
                plan_info["fully_done"],
                current_plan_id,
                all_plans_dict,
            )
            plan_info["status"] = status

        if filter_status:
            plans_data = [p for p in plans_data if p["status"] == filter_status]

        match sort_by:
            case "default":
                status_order = {"작업 가능": 0, "작업중": 1, "의존성 대기중": 2, "완료됨": 3}
                plans_data.sort(key=lambda p: _get_sort_key(p, status_order))
            case "name":
                plans_data.sort(key=lambda p: p["name"])
            case "created":
                plans_data.sort(key=lambda p: p["created_at"])

            case _:
                pass
        table = Table(title="Available Plans")
        table.add_column("Name", style="cyan")
        table.add_column("File Path", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Dependencies", justify="right")
        table.add_column("Created At")

        for plan in plans_data:
            match plan["status"]:
                case "작업중":
                    status_str = "[bright_green]작업중[/bright_green]"
                case "작업 가능":
                    status_str = "[bright_blue]작업 가능[/bright_blue]"
                case "완료됨":
                    status_str = "[dim]완료됨[/dim]"
                case "의존성 대기중":
                    status_str = "[bright_yellow]의존성 대기중[/bright_yellow]"
                case _:
                    status_str = plan["status"]

            try:
                dt = datetime.fromisoformat(plan["created_at"].replace("Z", "+00:00"))
                created_at_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                created_at_str = plan["created_at"]

            table.add_row(
                plan["name"],
                plan["filepath"],
                status_str,
                str(plan["dependency_count"]),
                created_at_str,
            )

        console.print(table)

    anyio.run(_list_plans_async)
