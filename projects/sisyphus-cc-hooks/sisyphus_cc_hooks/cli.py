"""CLI entry point for sisyphus-cc-hooks."""

from __future__ import annotations

import typer

from sisyphus_cc_hooks.post_tool_use_executor_verification import main as verification_main

app = typer.Typer(name="sisyphus-cc-hooks", help="Claude Code hooks for Sisyphus task verification")


@app.command(name="post-tool-use")
def post_tool_use() -> None:
    """Execute post-tool-use hook for executor verification.

    Reads JSON from stdin, validates executor completion,
    and outputs verification instructions to stderr.
    """
    exit_code = verification_main()
    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()
