from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from sisyphus_core.core.plans.models import PlanRegistry


def load_registry(registry_path: Path) -> PlanRegistry:
    """Load registry.yaml file.

    Args:
        registry_path: Path to registry.yaml file

    Returns:
        PlanRegistry instance

    Raises:
        FileNotFoundError: If registry file doesn't exist
        ValueError: If YAML is invalid
    """
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")

    with open(registry_path) as f:
        content = f.read()

    yaml = YAML()
    data = yaml.load(content)

    return PlanRegistry.model_validate(data)


def resolve_registry_plan(
    plan_id: str,
    registry: PlanRegistry,
    base_path: Path,
) -> tuple[Path, str]:
    """Resolve registry:plan-id format to file path and plan ID.

    Args:
        plan_id: Plan ID to resolve
        registry: Loaded PlanRegistry instance
        base_path: Base directory path (usually .sisyphus/)

    Returns:
        Tuple of (file_path, plan_id)

    Raises:
        ValueError: If plan_id not found in registry
    """
    for entry in registry.plans:
        if plan_id in entry.plans:
            file_path = base_path / entry.file
            return (file_path, plan_id)

    raise ValueError(f"Plan '{plan_id}' not found in registry")
