from io import StringIO
from pathlib import Path

import anyio
from ruamel.yaml import YAML

from sisyphus_core.core.plans.models import PlanDocument
from sisyphus_core.core.status.manager import StatusManager


async def load_plan(path: Path) -> PlanDocument:
    """
    Load a plan file with automatic version detection.

    Args:
        path: Path to YAML plan file

    Returns:
        PlanDocument for v3.0 files

    Raises:
        ValueError: If version is not 3.0, YAML is invalid, or version missing
        FileNotFoundError: If file doesn't exist
    """
    async with await anyio.open_file(path, "r") as f:
        content = await f.read()

    yaml = YAML()
    data = yaml.load(content)

    version = data.get("version")
    if not version:
        raise ValueError(f"Plan file {path} missing 'version' field")

    if version == "3.0":
        return PlanDocument(**data)
    else:
        raise ValueError(f"Unsupported version: {version}. Only v3.0 supported.")


def _discover_plan_files(root: Path) -> list[Path]:
    tasks_dir = root / ".sisyphus" / "tasks"
    if not tasks_dir.exists():
        return []
    return list(tasks_dir.glob("**/*.y*ml"))


async def load_multiple_plans(root: Path) -> dict[str, PlanDocument]:
    """
    Load all plan files from .sisyphus/tasks/ directory.

    Args:
        root: Worktree root path

    Returns:
        Dict of plan_id -> PlanDocument

    Raises:
        ValueError: If any plan is not v3.0, has invalid YAML, or missing version
    """
    plan_files = _discover_plan_files(root)

    if not plan_files:
        return {}

    plans: dict[str, PlanDocument] = {}
    errors: list[str] = []

    for plan_file in plan_files:
        try:
            plan_doc = await load_plan(plan_file)

            if not plan_doc.work_plans:
                errors.append(f"{plan_file}: No work_plans found")
                continue

            plan_id = plan_doc.work_plans[0].id
            plans[plan_id] = plan_doc

        except Exception as e:
            errors.append(f"{plan_file}: {e}")

    if errors:
        error_msg = "\n".join(errors)
        raise ValueError(f"Failed to load some plans:\n{error_msg}")

    return plans


async def save_plan(path: Path, plan_doc: PlanDocument) -> None:
    """
    Save a PlanDocument to YAML file.

    Args:
        path: Path to YAML file
        plan_doc: PlanDocument to save

    Raises:
        OSError: If file cannot be written
    """
    yaml = YAML()
    stream = StringIO()
    content = plan_doc.model_dump(mode="json", exclude_none=True)
    yaml.dump(content, stream)

    async with await anyio.open_file(path, "w") as f:
        _ = await f.write(stream.getvalue())


async def resolve_current_plan_from_status(root: Path) -> PlanDocument | None:
    """
    Resolve current plan from status.json.

    Args:
        root: Worktree root path

    Returns:
        PlanDocument if current_plan is set, None otherwise

    Raises:
        FileNotFoundError: If current plan file doesn't exist
        ValueError: If plan is not v3.0
    """
    status_path = root / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)

    status = await manager.get()

    if status.current_plan is None:
        return None

    plan_path = root / status.current_plan.plan_path
    return await load_plan(plan_path)
