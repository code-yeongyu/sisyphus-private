from pathlib import Path

import anyio
from ruamel.yaml import YAML

from sisyphus.core.plans.exceptions import UnsupportedPlanVersionError
from sisyphus.core.plans.models import PlanDocument


async def load_plan(path: Path) -> PlanDocument:
    """
    Load a plan file with automatic version detection.

    Args:
        path: Path to YAML plan file

    Returns:
        PlanDocument for v3.0 files

    Raises:
        UnsupportedPlanVersionError: If version is not 3.0
        FileNotFoundError: If file doesn't exist
        ValueError: If YAML is invalid or version missing
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
    elif version in ("2.1", "2.0"):
        raise UnsupportedPlanVersionError(
            f"Plan version {version} is not supported. Please use 'sisyphus plan convert-legacy' to migrate to v3.0"
        )
    else:
        raise ValueError(f"Unknown plan version: {version}")
