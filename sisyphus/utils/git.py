"""Git utility functions for Sisyphus."""

from __future__ import annotations

import subprocess
from fnmatch import fnmatch
from pathlib import Path


def run_git_command(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run git command and return (returncode, stdout, stderr).

    Args:
        args: List of git command arguments
        cwd: Working directory (optional)

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return (result.returncode, result.stdout.strip(), result.stderr.strip())
    except FileNotFoundError:
        return (127, "", "git command not found")


def detect_base_branch() -> str | None:
    """Detect base branch (origin/main > origin/master > origin/develop).

    Returns:
        Base branch name or None if not found
    """
    candidates = ["origin/main", "origin/master", "origin/develop"]
    for branch in candidates:
        returncode, stdout, _ = run_git_command(["show-ref", "--verify", f"refs/remotes/{branch}"])
        if returncode == 0:
            return branch
    return None


def is_on_main_branch() -> bool:
    """Check if current branch is main/master.

    Returns:
        True if on main or master branch
    """
    returncode, stdout, _ = run_git_command(["branch", "--show-current"])
    if returncode == 0:
        current_branch = stdout.strip()
        return current_branch in ("main", "master")
    return False


def _matches_pattern(file: str, patterns: list[str]) -> bool:
    """Check if file matches any pattern (exact, directory prefix, or glob).

    Args:
        file: File path to check
        patterns: List of patterns (files, directories ending with /, or glob patterns)

    Returns:
        True if file matches any pattern

    Examples:
        _matches_pattern("ai-todolist.md", ["ai-todolist.md"]) → True
        _matches_pattern("sessions/test.json", ["sessions/"]) → True
        _matches_pattern("claude_session_abc.log", ["claude_session_*.log"]) → True
        _matches_pattern("other.txt", ["ai-todolist.md"]) → False
    """
    for pattern in patterns:
        if pattern.endswith("/"):
            # Directory pattern: check if file is inside
            dir_name = pattern.rstrip("/")
            if file.startswith(dir_name + "/") or file == dir_name:
                return True
        elif "*" in pattern or "?" in pattern or "[" in pattern:
            # Glob pattern: use fnmatch
            if fnmatch(file, pattern):
                return True
        else:
            # File pattern: exact match
            if file == pattern:
                return True
    return False


def find_commits_with_files(base_branch: str, file_patterns: list[str]) -> list[dict[str, str | list[str]]]:
    """Find commits containing specified files since base branch.

    Args:
        base_branch: Base branch name (e.g., "origin/main")
        file_patterns: List of file patterns to search for

    Returns:
        List of {"hash": str, "message": str, "files": list[str]}
    """
    returncode, stdout, _ = run_git_command(
        ["log", "--pretty=format:%H%x1f%s%x1f", "--name-only", "-z", "--no-merges", f"{base_branch}..HEAD"]
    )
    if returncode != 0:
        return []

    commits = []
    entries = stdout.split("\0")
    i = 0

    while i < len(entries):
        if not entries[i].strip():
            i += 1
            continue

        # Each commit starts with "HASH\x1fMESSAGE\x1f" format
        commit_line = entries[i].strip()

        # Split by unit separator to get hash and message
        parts = commit_line.split("\x1f")
        if len(parts) < 2:
            # Malformed entry, skip
            i += 1
            continue

        commit_hash = parts[0]
        message = parts[1]
        i += 1

        # Following entries are file paths until next commit or end
        files = []
        while i < len(entries):
            entry = entries[i].strip()
            if not entry:
                # Empty entry marks end of file list
                i += 1
                break
            # Check if this is the start of next commit (contains \x1f)
            if "\x1f" in entry:
                # Next commit, don't consume
                break
            files.append(entry)
            i += 1

        # Check if any file matches patterns using helper
        matching_files = []
        for f in files:
            if _matches_pattern(f, file_patterns):
                matching_files.append(f)

        if matching_files:
            commits.append(
                {
                    "hash": commit_hash,
                    "message": message,
                    "files": matching_files,
                }
            )

    return commits


def generate_rebase_guide(commits: list[dict[str, str | list[str]]], base_branch: str) -> str:
    """Generate interactive rebase guide for removing files.

    Args:
        commits: List of {"hash": str, "message": str, "files": list[str]}
        base_branch: Base branch name (e.g., "origin/main")

    Returns:
        Formatted guide string with Rich markup
    """
    lines = []
    lines.append("[bold yellow]⚠ Git History Cleanup Guide[/bold yellow]\n")
    lines.append(
        f"Found [bold]{len(commits)} commit(s)[/bold] containing Sisyphus files since [cyan]{base_branch}[/cyan]:\n"
    )

    # List affected commits
    for i, commit in enumerate(commits, 1):
        hash_short = commit["hash"][:7]
        lines.append(f"[bold]{i}. {hash_short}[/bold] - {commit['message']}")
        lines.append(f"   Files: {', '.join(commit['files'])}\n")

    # Step-by-step instructions
    lines.append("[bold green]Step-by-step cleanup instructions:[/bold green]\n")
    lines.append("1. Start interactive rebase:")
    lines.append(f"   [dim]$[/dim] git rebase -i {base_branch}\n")

    lines.append("2. In the editor, change [bold]pick[/bold] to [bold]edit[/bold] for these commits:")
    for commit in commits:
        hash_short = commit["hash"][:7]
        lines.append(f"   • {hash_short} ({commit['message']})")
    lines.append("")

    lines.append("3. For each commit marked 'edit', run:")
    for commit in commits:
        hash_short = commit["hash"][:7]
        files_str = " ".join(f'"{f}"' if " " in f else f for f in commit["files"])
        lines.append(f"   [dim]$[/dim] git rm {files_str}  # For {hash_short}")
        lines.append("   [dim]$[/dim] git commit --amend --no-edit")
        lines.append("   [dim]$[/dim] git rebase --continue\n")

    lines.append("4. Verify cleanup:")
    lines.append(f"   [dim]$[/dim] git log --name-only {base_branch}..HEAD\n")

    lines.append("[yellow]Note:[/yellow] If you've already pushed these commits, you'll need to force push:")
    lines.append("   [dim]$[/dim] git push --force-with-lease")

    return "\n".join(lines)
