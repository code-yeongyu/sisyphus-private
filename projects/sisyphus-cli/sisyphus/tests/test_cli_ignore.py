"""Tests for sisyphus ignore command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus.cli import app

pytestmark = [pytest.mark.anyio]


def test_ignore__default__adds_to_gitignore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore"])

    # then
    assert result.exit_code == 0
    gitignore_path = tmp_path / ".gitignore"
    assert gitignore_path.exists()
    gitignore_content = gitignore_path.read_text()
    assert ".sisyphus/" in gitignore_content
    assert "sessions/" in gitignore_content
    assert "# Sisyphus generated files" in gitignore_content


def test_ignore__exclude_only__adds_only_to_exclude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore", "--exclude-only"])

    # then
    assert result.exit_code == 0
    exclude_path = git_dir / "info" / "exclude"
    assert exclude_path.exists()
    exclude_content = exclude_path.read_text()
    assert ".sisyphus/" in exclude_content
    assert "sessions/" in exclude_content

    gitignore_path = tmp_path / ".gitignore"
    assert not gitignore_path.exists()


def test_ignore__both__adds_to_both_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore", "--both"])

    # then
    assert result.exit_code == 0
    gitignore_path = tmp_path / ".gitignore"
    assert gitignore_path.exists()
    gitignore_content = gitignore_path.read_text()
    assert ".sisyphus/" in gitignore_content

    exclude_path = git_dir / "info" / "exclude"
    assert exclude_path.exists()
    exclude_content = exclude_path.read_text()
    assert ".sisyphus/" in exclude_content


def test_ignore__duplicate_prevention__skips_existing_patterns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(".sisyphus/\n")

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore"])

    # then
    assert result.exit_code == 0
    gitignore_content = gitignore_path.read_text()
    assert gitignore_content.count(".sisyphus/") == 1
    assert "sessions/" in gitignore_content


def test_ignore__no_git_directory__returns_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore"])

    # then
    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "git repository" in output or "Not in a git repository" in output


def test_ignore__both_and_exclude_only_flags__returns_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore", "--both", "--exclude-only"])

    # then
    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "Cannot use both" in output


def test_ignore__creates_git_info_directory_if_needed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore", "--exclude-only"])

    # then
    assert result.exit_code == 0
    info_dir = git_dir / "info"
    assert info_dir.exists()
    exclude_path = info_dir / "exclude"
    assert exclude_path.exists()


def test_ignore__existing_gitignore_with_content__preserves_existing_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    gitignore_path = tmp_path / ".gitignore"
    existing_content = "# My custom ignores\n*.pyc\n"
    gitignore_path.write_text(existing_content)

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore"])

    # then
    assert result.exit_code == 0
    gitignore_content = gitignore_path.read_text()
    assert "*.pyc" in gitignore_content
    assert ".sisyphus/" in gitignore_content


def test_ignore__all_patterns_already_exist__shows_no_changes_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # given
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "info").mkdir()

    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(
        "# Sisyphus generated files\n.sisyphus/\nnotepad.md\nsessions/\nlogs/\nagentloop.json\nclaude_session_*.log\n"
    )

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # when
    result = runner.invoke(app, ["ignore"])

    # then
    assert result.exit_code == 0
    assert "already present" in result.stdout or "No changes made" in result.stdout
