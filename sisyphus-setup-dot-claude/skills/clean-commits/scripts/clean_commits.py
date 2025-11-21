#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.12.0",
#     "rich>=13.0.0",
# ]
# ///
# pyright: reportMissingImports=false

import asyncio
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID

app = typer.Typer()
console = Console()


async def run_git_command(*args: str, check: bool = True) -> tuple[int, str, str]:
    """Run git command and return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        "git",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = await proc.communicate()
    stdout = stdout_bytes.decode().strip()
    stderr = stderr_bytes.decode().strip()

    if check and proc.returncode != 0:
        console.print(f"[red]✗ Git command failed: git {' '.join(args)}[/red]")
        console.print(f"[red]{stderr}[/red]")
        sys.exit(proc.returncode)

    return proc.returncode or 0, stdout, stderr


async def detect_base_branch() -> str | None:
    """Detect base branch using updatebranch script or git config."""
    # Try ~/other/updatebranch
    updatebranch_path = Path.home() / "other" / "updatebranch"
    if updatebranch_path.exists():
        try:
            proc = await asyncio.create_subprocess_exec(
                str(updatebranch_path),
                "--detect-base",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, _ = await proc.communicate()
            if proc.returncode == 0:
                base = stdout_bytes.decode().strip()
                if base:
                    return base
        except Exception:
            pass

    # Try common base branches
    _, branches, _ = await run_git_command("branch", "-a", check=False)
    common_bases = ["main", "master", "develop", "dev"]

    for base in common_bases:
        if f"origin/{base}" in branches or base in branches:
            return base

    return None


async def get_uncommitted_changes() -> bool:
    """Check if there are uncommitted changes."""
    _, status, _ = await run_git_command("status", "--porcelain", check=False)
    return bool(status.strip())


async def find_target_commit_for_fixup(file_path: str) -> str | None:
    """Find the most recent commit that modified the given file."""
    _, log_output, _ = await run_git_command(
        "log",
        "--pretty=format:%H",
        "-n",
        "10",
        "--",
        file_path,
        check=False,
    )

    commits = log_output.split("\n")
    return commits[0] if commits and commits[0] else None


@app.command()
def main(
    base_branch: Annotated[
        str | None, typer.Argument(help="Base branch to rebase onto (auto-detected if not provided)")
    ] = None,
    force: Annotated[bool, typer.Option("-f", "--force", help="Force rebase even with conflicts")] = False,
) -> None:
    """Clean up commits using git absorb and autosquash rebase.

    This tool automatically:
    1. Stages all changes
    2. Runs git absorb to integrate changes into existing commits
    3. Creates fixup commits for remaining changes
    4. Performs autosquash rebase with autoStash and rerere enabled
    """

    async def async_main() -> None:
        # Step 1: Detect base branch
        detected_base = base_branch
        if not detected_base:
            console.print("[cyan]Detecting base branch...[/cyan]")
            detected_base = await detect_base_branch()

            if not detected_base:
                console.print("[yellow]⚠ Could not auto-detect base branch[/yellow]")
                detected_base = typer.prompt("Enter base branch name")

        console.print(f"""
[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]
[cyan]Base branch: {detected_base}[/cyan]
[cyan]Force mode: {"Yes" if force else "No"}[/cyan]
[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]
""")

        with Progress(console=console) as progress:
            task: TaskID = progress.add_task("[cyan]Cleaning commits...", total=5)

            # Step 2: Stage all changes
            progress.update(task, advance=1, description="[cyan]Staging changes... (1/5)")
            _ = await run_git_command("add", ".")
            console.print("[green]✓[/green] Staged all changes")

            # Step 3: Run git absorb with rebase
            progress.update(task, advance=1, description="[cyan]Running git absorb... (2/5)")

            force_flag = "--force" if force else ""
            returncode, _stdout, stderr = await run_git_command(
                "absorb",
                "--and-rebase",
                force_flag,
                "-c",
                "rebase.autosquash=true",
                "-c",
                "rebase.autoStash=true",
                "-c",
                "rerere.enabled=true",
                detected_base,
                check=False,
            )

            if returncode != 0:
                console.print("[yellow]⚠ git absorb completed with warnings[/yellow]")
                if stderr:
                    console.print(f"[dim]{stderr}[/dim]")
            else:
                console.print("[green]✓[/green] git absorb completed")

            # Step 4: Check for remaining changes
            progress.update(task, advance=1, description="[cyan]Checking remaining changes... (3/5)")

            has_changes = await get_uncommitted_changes()

            if has_changes:
                console.print("[yellow]⚠ Found uncommitted changes after absorb[/yellow]")

                # Get list of modified files
                _, status_output, _ = await run_git_command("status", "--porcelain")
                modified_files: list[str] = []
                for line in status_output.split("\n"):
                    if line.strip():
                        # Parse git status format: "XY filename"
                        parts = line.strip().split(maxsplit=1)
                        if len(parts) == 2:
                            modified_files.append(parts[1])

                if modified_files:
                    console.print(f"[cyan]Creating fixup commits for {len(modified_files)} files...[/cyan]")

                    # Step 5: Create fixup commits
                    progress.update(task, advance=1, description="[cyan]Creating fixup commits... (4/5)")

                    for file_path in modified_files:
                        target_commit = await find_target_commit_for_fixup(file_path)

                        if target_commit:
                            # Stage the file
                            _ = await run_git_command("add", file_path)

                            # Create fixup commit
                            _ = await run_git_command(
                                "commit",
                                "--fixup",
                                target_commit,
                                check=False,
                            )
                            console.print(f"[green]✓[/green] Created fixup commit for {file_path}")
                        else:
                            console.print(f"[yellow]⚠ Could not find target commit for {file_path}, skipping[/yellow]")

                    # Step 6: Run autosquash rebase
                    progress.update(task, advance=1, description="[cyan]Running autosquash rebase... (5/5)")

                    _ = await run_git_command(
                        "rebase",
                        "-i",
                        "--autosquash",
                        "-c",
                        "rebase.autoStash=true",
                        "-c",
                        "rerere.enabled=true",
                        detected_base,
                        check=False,
                    )
                    console.print("[green]✓[/green] Autosquash rebase completed")
                else:
                    progress.update(task, advance=2)
            else:
                console.print("[green]✓[/green] No remaining changes")
                progress.update(task, advance=2)

        # Final status check
        final_has_changes = await get_uncommitted_changes()

        if final_has_changes:
            panel = Panel(
                "[yellow]⚠ Some changes could not be automatically committed\n"
                + "Please review and commit manually[/yellow]",
                title="[yellow]Partially Complete[/yellow]",
                border_style="yellow",
            )
        else:
            panel = Panel(
                f"[green]✓ All commits cleaned successfully\nRebased onto: {detected_base}[/green]",
                title="[green]Complete[/green]",
                border_style="green",
            )

        console.print(panel)

    asyncio.run(async_main())


if __name__ == "__main__":
    app()
