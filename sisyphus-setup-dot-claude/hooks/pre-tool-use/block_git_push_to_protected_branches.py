#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import asyncio
import json
import sys
from typing import NotRequired, TypedDict


class ToolInput(TypedDict):
    command: NotRequired[str]
    description: NotRequired[str]
    timeout: NotRequired[int]
    run_in_background: NotRequired[bool]


class PreToolUseInput(TypedDict):
    tool_name: str
    tool_input: ToolInput
    working_directory: str


async def get_current_branch(working_dir: str) -> str | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "branch",
            "--show-current",
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        if proc.returncode == 0:
            return stdout.decode().strip()
    except Exception:
        pass
    return None


async def get_github_default_branch(working_dir: str) -> str | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "remote",
            "get-url",
            "origin",
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        if proc.returncode != 0:
            return None

        remote_url = stdout.decode().strip()

        if "github.com" not in remote_url:
            return None

        if remote_url.startswith("git@github.com:"):
            repo_path = remote_url.replace("git@github.com:", "").replace(".git", "")
        elif "github.com/" in remote_url:
            repo_path = remote_url.split("github.com/")[1].replace(".git", "")
        else:
            return None

        proc = await asyncio.create_subprocess_exec(
            "gh",
            "api",
            f"repos/{repo_path}",
            "--jq",
            ".default_branch",
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)

        if proc.returncode == 0:
            return stdout.decode().strip()
    except Exception:
        pass
    return None


async def get_protected_branches(working_dir: str) -> set[str]:
    protected = {"main", "master", "develop", "production", "staging"}

    github_default = await get_github_default_branch(working_dir)
    if github_default:
        protected.add(github_default)

    return protected


def is_git_push_command(command: str) -> bool:
    normalized = " ".join(command.split())

    patterns = [
        "git push",
        "git push ",
        "&& git push",
        "; git push",
        "| git push",
    ]

    return any(pattern in normalized for pattern in patterns)


async def main() -> int:
    try:
        input_data: PreToolUseInput = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        working_dir = input_data.get("working_directory", ".")

        if tool_name != "Bash":
            return 0

        command = tool_input.get("command", "")
        if not command:
            return 0

        if not is_git_push_command(command):
            return 0

        current_branch = await get_current_branch(working_dir)
        if not current_branch:
            return 0

        protected_branches = await get_protected_branches(working_dir)

        if current_branch in protected_branches:
            error_message = f"""
[GIT PUSH BLOCKED]
❌ Direct push to protected branch '{current_branch}' is not allowed!

Protected branches: {", ".join(sorted(protected_branches))}

💡 Recommended workflow:
   1. Create a feature branch:
      git checkout -b feature/your-feature-name

   2. Make your changes and commit

   3. Push to feature branch:
      git push -u origin feature/your-feature-name

   4. Create a Pull Request on GitHub

"""
            print(error_message, file=sys.stderr)
            return 2

        return 0

    except json.JSONDecodeError:
        return 0
    except Exception as e:
        print(f"⚠️  Hook error (allowing operation): {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
