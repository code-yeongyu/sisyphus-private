from __future__ import annotations

import io
import json
import sys
from typing import Any

import typer

from .post_tool_use_executor_verification import main as verification_main
from .post_tool_use_plan_lint import main as plan_lint_main

app = typer.Typer(name="sisyphus-cc-hooks", help="Claude Code hooks for Sisyphus task verification")


@app.command(name="post-tool-use")
def post_tool_use() -> None:
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        data: dict[str, Any] = json.loads(input_raw)
    except json.JSONDecodeError:
        sys.exit(0)

    subagent_type = data.get("tool_input", {}).get("subagent_type", "")

    if subagent_type == "sisyphus-executor":
        sys.stdin = io.StringIO(input_raw)
        exit_code = verification_main()
        sys.exit(exit_code)

    sys.stdin = io.StringIO(input_raw)
    exit_code = plan_lint_main()
    sys.exit(exit_code)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "post-tool-use":
        sys.argv = [sys.argv[0]]
        post_tool_use()
    else:
        app()


if __name__ == "__main__":
    main()
