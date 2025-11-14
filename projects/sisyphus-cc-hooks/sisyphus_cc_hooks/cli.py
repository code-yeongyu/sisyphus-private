from __future__ import annotations

import sys

import typer  # type: ignore[import-not-found]

from .post_tool_use import main as post_tool_use_main
from .pre_tool_use import main as pre_tool_use_main

app = typer.Typer(
    name="sisyphus-cc-hooks",
    help="Claude Code hooks for sisyphus-speckit task verification",
)


@app.command(name="pre-tool-use")
def pre_tool_use() -> None:
    exit_code = pre_tool_use_main()
    sys.exit(exit_code)


@app.command(name="post-tool-use")
def post_tool_use() -> None:
    exit_code = post_tool_use_main()
    sys.exit(exit_code)


def main() -> None:
    if len(sys.argv) <= 1:
        app()
        return

    match sys.argv[1]:
        case "pre-tool-use":
            sys.argv = [sys.argv[0]]
            pre_tool_use()
        case "post-tool-use":
            sys.argv = [sys.argv[0]]
            post_tool_use()
        case _:
            app()


if __name__ == "__main__":
    main()
