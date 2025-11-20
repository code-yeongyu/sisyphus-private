"""Tests for sisyphus clean-history command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from ..cli import app

pytestmark = [pytest.mark.anyio]


def test_clean_history__on_main_branch__exits_with_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main:
        mock_on_main.return_value = True
        result = runner.invoke(app, ["clean-history"])

    # then
    assert result.exit_code == 1
    assert "Cannot clean history on main/master branch" in result.output


def test_clean_history__no_base_branch_detected__exits_with_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.detect_base_branch") as mock_detect,
    ):
        mock_on_main.return_value = False
        mock_detect.return_value = None
        result = runner.invoke(app, ["clean-history"])

    # then
    assert result.exit_code == 1
    assert "No base branch found" in result.output
    assert "origin/main" in result.output


def test_clean_history__with_base_branch_option__uses_specified_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.find_commits_with_files") as mock_find,
    ):
        mock_on_main.return_value = False
        mock_find.return_value = []
        result = runner.invoke(app, ["clean-history", "--base-branch", "origin/develop"])

    # then
    assert result.exit_code == 0
    mock_find.assert_called_once()
    call_args = mock_find.call_args
    assert call_args[0][0] == "origin/develop"


def test_clean_history__no_commits_found__shows_success_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.detect_base_branch") as mock_detect,
        patch("sisyphus.cli.work.find_commits_with_files") as mock_find,
    ):
        mock_on_main.return_value = False
        mock_detect.return_value = "origin/main"
        mock_find.return_value = []
        result = runner.invoke(app, ["clean-history"])

    # then
    assert result.exit_code == 0
    assert "No commits containing Sisyphus files found" in result.output
    assert "Git history is clean" in result.output


def test_clean_history__with_commits__shows_warning_and_guide(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    commits = [
        {
            "hash": "abc123def456",
            "message": "Add feature",
            "files": [".sisyphus/tasks/test.yaml", "sessions/test.json"],
        },
        {
            "hash": "def456ghi789",
            "message": "Update logs",
            "files": ["logs/test.log"],
        },
    ]

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.detect_base_branch") as mock_detect,
        patch("sisyphus.cli.work.find_commits_with_files") as mock_find,
    ):
        mock_on_main.return_value = False
        mock_detect.return_value = "origin/main"
        mock_find.return_value = commits
        result = runner.invoke(app, ["clean-history"], input="n\n")

    # then
    assert result.exit_code == 0
    assert "Warning: Git History Modification" in result.output
    assert "Found 2 commit(s)" in result.output
    assert "Do you want to proceed?" in result.output
    assert "Operation cancelled" in result.output


def test_clean_history__user_confirms__shows_rebase_guide(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    commits = [
        {
            "hash": "abc123def456",
            "message": "Add feature",
            "files": [".sisyphus/tasks/test.yaml"],
        }
    ]

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.detect_base_branch") as mock_detect,
        patch("sisyphus.cli.work.find_commits_with_files") as mock_find,
        patch("sisyphus.cli.work.generate_rebase_guide") as mock_guide,
    ):
        mock_on_main.return_value = False
        mock_detect.return_value = "origin/main"
        mock_find.return_value = commits
        mock_guide.return_value = (
            "[bold yellow]⚠ Git History Cleanup Guide[/bold yellow]\n\nFound [bold]1 commit(s)[/bold]"
        )
        result = runner.invoke(app, ["clean-history"], input="y\n")

    # then
    assert result.exit_code == 0
    assert "Git History Cleanup Guide" in result.output
    mock_guide.assert_called_once_with(commits, "origin/main")


def test_clean_history__dry_run_mode__skips_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    commits = [
        {
            "hash": "abc123def456",
            "message": "Add feature",
            "files": [".sisyphus/tasks/test.yaml"],
        }
    ]

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.detect_base_branch") as mock_detect,
        patch("sisyphus.cli.work.find_commits_with_files") as mock_find,
        patch("sisyphus.cli.work.generate_rebase_guide") as mock_guide,
    ):
        mock_on_main.return_value = False
        mock_detect.return_value = "origin/main"
        mock_find.return_value = commits
        mock_guide.return_value = "[bold yellow]⚠ Git History Cleanup Guide[/bold yellow]"
        result = runner.invoke(app, ["clean-history", "--dry-run"])

    # then
    assert result.exit_code == 0
    assert "DRY RUN - no changes made" in result.output
    assert "Do you want to proceed?" not in result.output


def test_clean_history__user_declines__exits_gracefully(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    commits = [
        {
            "hash": "abc123def456",
            "message": "Add feature",
            "files": [".sisyphus/tasks/test.yaml"],
        }
    ]

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.detect_base_branch") as mock_detect,
        patch("sisyphus.cli.work.find_commits_with_files") as mock_find,
    ):
        mock_on_main.return_value = False
        mock_detect.return_value = "origin/main"
        mock_find.return_value = commits
        result = runner.invoke(app, ["clean-history"], input="n\n")

    # then
    assert result.exit_code == 0
    assert "Operation cancelled" in result.output


def test_clean_history__autodetects_base_branch_when_not_specified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.detect_base_branch") as mock_detect,
        patch("sisyphus.cli.work.find_commits_with_files") as mock_find,
    ):
        mock_on_main.return_value = False
        mock_detect.return_value = "origin/master"
        mock_find.return_value = []
        result = runner.invoke(app, ["clean-history"])

    # then
    assert result.exit_code == 0
    mock_detect.assert_called_once()
    call_args = mock_find.call_args
    assert call_args[0][0] == "origin/master"


def test_clean_history__passes_file_patterns_to_find_commits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    with (
        patch("sisyphus.cli.work.is_on_main_branch") as mock_on_main,
        patch("sisyphus.cli.work.detect_base_branch") as mock_detect,
        patch("sisyphus.cli.work.find_commits_with_files") as mock_find,
    ):
        mock_on_main.return_value = False
        mock_detect.return_value = "origin/main"
        mock_find.return_value = []
        result = runner.invoke(app, ["clean-history"])

    # then
    assert result.exit_code == 0
    call_args = mock_find.call_args
    file_patterns = call_args[0][1]
    assert ".sisyphus/" in file_patterns
    assert "notepad.md" in file_patterns
    assert "sessions/" in file_patterns
    assert "logs/" in file_patterns
    assert "agentloop.json" in file_patterns
    assert "claude_session_*.log" in file_patterns
