from __future__ import annotations

import importlib.util
from pathlib import Path

from sisyphus.cli.reset import reset_app as reset_app

cli_module_path = Path(__file__).parent.parent / "cli.py"
spec = importlib.util.spec_from_file_location("sisyphus_cli_main", cli_module_path)
if spec and spec.loader:
    cli_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli_module)
    app = cli_module.app
else:
    raise ImportError("Could not load sisyphus.cli module")
