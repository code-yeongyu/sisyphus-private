"""Tests for git utility functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sisyphus_core.utils.git import (
    _matches_pattern,
    detect_base_branch,
    find_commits_with_files,
    generate_rebase_guide,
    is_on_main_branch,
    run_git_command,
)

pytestmark = [pytest.mark.anyio]


def test_run_git_command__if_command_succeeds__returns_tuple() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="master",
            stderr="",
        )

        # when
        returncode, stdout, stderr = run_git_command(["branch", "--show-current"])

        # then
        assert returncode == 0
        assert stdout == "master"
        assert stderr == ""
        mock_run.assert_called_once()


def test_run_git_command__if_git_not_found__returns_error_code() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()

        # when
        returncode, stdout, stderr = run_git_command(["branch"])

        # then
        assert returncode == 127
        assert stdout == ""
        assert stderr == "git command not found"


def test_detect_base_branch__if_origin_main_exists__returns_origin_main() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="refs/remotes/origin/main",
            stderr="",
        )

        # when
        result = detect_base_branch()

        # then
        assert result == "origin/main"


def test_detect_base_branch__if_no_branch_exists__returns_none() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="",
        )

        # when
        result = detect_base_branch()

        # then
        assert result is None


def test_is_on_main_branch__if_on_main__returns_true() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="main",
            stderr="",
        )

        # when
        result = is_on_main_branch()

        # then
        assert result is True


def test_is_on_main_branch__if_on_master__returns_true() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="master",
            stderr="",
        )

        # when
        result = is_on_main_branch()

        # then
        assert result is True


def test_is_on_main_branch__if_on_feature_branch__returns_false() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="feature-branch",
            stderr="",
        )

        # when
        result = is_on_main_branch()

        # then
        assert result is False


def test_matches_pattern__with_exact_file__returns_true() -> None:
    # given
    # when
    result = _matches_pattern("ai-todolist.md", ["ai-todolist.md"])

    # then
    assert result is True


def test_matches_pattern__with_directory__returns_true() -> None:
    # given
    # when
    result = _matches_pattern("sessions/test.json", ["sessions/"])

    # then
    assert result is True


def test_matches_pattern__with_glob__returns_true() -> None:
    # given
    # when
    result1 = _matches_pattern("claude_session_abc123.log", ["claude_session_*.log"])
    result2 = _matches_pattern("other.log", ["claude_session_*.log"])

    # then
    assert result1 is True
    assert result2 is False


def test_matches_pattern__with_no_match__returns_false() -> None:
    # given
    # when
    result = _matches_pattern("other.txt", ["ai-todolist.md", "sessions/"])

    # then
    assert result is False


def test_find_commits_with_files__if_commits_found__returns_list() -> None:
    # given
    mock_stdout = (
        "abc123\x1fAdd feature\x1f\nai-todolist.md\nsessions/test.json\x00\x00"
        "def456\x1fAnother commit\x1f\nlogs/test.log\x00"
    )
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_stdout,
            stderr="",
        )

        # when
        result = find_commits_with_files("origin/main", ["ai-todolist.md", "sessions/", "logs/"])

        # then
        assert len(result) == 2
        assert result[0]["hash"] == "abc123"
        assert result[0]["message"] == "Add feature"
        assert "ai-todolist.md" in result[0]["files"]
        assert "sessions/test.json" in result[0]["files"]
        assert result[1]["hash"] == "def456"
        assert result[1]["message"] == "Another commit"
        assert "logs/test.log" in result[1]["files"]


def test_find_commits_with_files__if_no_commits__returns_empty_list() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="",
        )

        # when
        result = find_commits_with_files("origin/main", ["ai-todolist.md"])

        # then
        assert result == []


def test_find_commits_with_files__if_no_files_match__returns_empty_list() -> None:
    # given
    with patch("sisyphus.utils.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123\x1fAdd feature\x1f\x00README.md\x00\x00",
            stderr="",
        )

        # when
        result = find_commits_with_files("origin/main", ["ai-todolist.md", "sessions/"])

        # then
        assert result == []


def test_generate_rebase_guide__if_commits_provided__returns_formatted_guide() -> None:
    # given
    commits = [
        {
            "hash": "abc1234567890",
            "message": "Add feature",
            "files": ["ai-todolist.md", "sessions/test.json"],
        },
        {
            "hash": "def1234567890",
            "message": "Another commit",
            "files": ["logs/test.log"],
        },
    ]

    # when
    result = generate_rebase_guide(commits, "origin/main")

    # then
    assert "⚠ Git History Cleanup Guide" in result
    assert "Found [bold]2 commit(s)[/bold]" in result
    assert "origin/main" in result
    assert "abc1234" in result
    assert "def1234" in result
    assert "git rebase -i origin/main" in result
    assert "git rm" in result
    assert "git commit --amend --no-edit" in result
    assert "git push --force-with-lease" in result
