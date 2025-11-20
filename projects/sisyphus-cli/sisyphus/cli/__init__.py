from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .reset import reset_app as reset_app

cli_module_path = Path(__file__).parent.parent / "cli.py"
spec = importlib.util.spec_from_file_location("sisyphus.cli_main", cli_module_path, submodule_search_locations=[str(Path(__file__).parent.parent)])
if spec and spec.loader:
    cli_module = importlib.util.module_from_spec(spec)
    sys.modules["sisyphus.cli_main"] = cli_module
    spec.loader.exec_module(cli_module)
    app = cli_module.app
else:
    raise ImportError("Could not load sisyphus.cli module")
