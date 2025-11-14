from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def should_run_sisyphus_plan_lint(tool_name: str, file_path: str) -> bool:
    if tool_name not in ["Write", "Edit"]:
        return False

    if not file_path:
        return False

    path = Path(file_path)

    if path.suffix != ".yaml":
        return False

    parts = path.parts
    try:
        sisyphus_idx = parts.index(".sisyphus")
        if sisyphus_idx + 1 < len(parts) and parts[sisyphus_idx + 1] == "tasks":
            return True
    except (ValueError, IndexError):
        pass

    return False


def run_sisyphus_plan_lint(yaml_path: str, cwd: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["sisyphus", "plan", "lint", "--file", yaml_path],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )

        if result.returncode == 0:
            return True, ""

        error_output = (
            result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
        )

        message = f"""
sisyphus-speckit plan YAML VALIDATION FAILED

File: {yaml_path}
Exit Code: {result.returncode}

{error_output}

REQUIRED ACTION:
The YAML file you just wrote/edited has validation errors.
You MUST fix these errors before proceeding.

FIX. NOW.

DO NOT proceed to the next task until validation passes.
""".strip()

        return False, message

    except subprocess.TimeoutExpired:
        return False, f"sisyphus-speckit plan lint timed out after 10s for {yaml_path}"
    except FileNotFoundError:
        return True, ""
    except Exception:
        return True, ""


def main() -> int:
    try:
        input_raw = sys.stdin.read()
        if not input_raw.strip():
            return 0

        data: dict[str, Any] = json.loads(input_raw)
    except json.JSONDecodeError:
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    cwd = data.get("cwd", ".")

    if not should_run_sisyphus_plan_lint(tool_name, file_path):
        return 0

    success, error_message = run_sisyphus_plan_lint(file_path, cwd)
    if not success and error_message:
        print(error_message, file=sys.stderr)
        return 2

    return 0
