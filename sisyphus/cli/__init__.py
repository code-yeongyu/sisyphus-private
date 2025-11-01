from __future__ import annotations

import importlib.util
from pathlib import Path

from sisyphus.cli.plan import plan_app as plan_app
from sisyphus.cli.reset import reset_app as reset_app
from sisyphus.cli.task import task_app as task_app

cli_module_path = Path(__file__).parent.parent / "cli.py"
spec = importlib.util.spec_from_file_location("sisyphus_cli_main", cli_module_path)
if spec and spec.loader:
    cli_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli_module)
    app = cli_module.app
else:
    raise ImportError("Could not load sisyphus.cli module")

__all__ = ["app", "plan_app", "task_app", "reset_app"]
