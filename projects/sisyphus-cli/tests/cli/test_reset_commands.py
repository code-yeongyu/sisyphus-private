from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus.cli.reset import reset_app

pytestmark = [pytest.mark.anyio]

runner = CliRunner()


def test_reset__with_no_files__shows_message(tmp_path: Path) -> None:
    # given: empty directory
    # when
    result = runner.invoke(reset_app, ["--cwd", str(tmp_path), "--yes"])

    # then
    assert result.exit_code == 0
    assert "No files or directories to delete" in result.stdout


def test_reset__with_base_files__deletes_them(tmp_path: Path) -> None:
    # given
    notepad = tmp_path / "notepad.md"
    sessions = tmp_path / "sessions"
    logs = tmp_path / "logs"

    notepad.write_text("test")
    sessions.mkdir()
    (sessions / "test.json").write_text("{}")
    logs.mkdir()
    (logs / "test.log").write_text("log")

    # when
    result = runner.invoke(reset_app, ["--cwd", str(tmp_path), "--yes"])

    # then
    assert result.exit_code == 0
    assert "Reset complete!" in result.stdout
    assert not notepad.exists()
    assert not sessions.exists()
    assert not logs.exists()


def test_reset__with_task_specs_flag__deletes_task_specs(tmp_path: Path) -> None:
    # given
    notepad = tmp_path / "notepad.md"
    notepad.write_text("test")

    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "plan.yaml").write_text("test")
    status_file = sisyphus_dir / "status.json"
    status_file.write_text("{}")

    # when
    result = runner.invoke(reset_app, ["--cwd", str(tmp_path), "--include-task-specs", "--yes"])

    # then
    assert result.exit_code == 0
    assert "Reset complete!" in result.stdout
    assert not notepad.exists()
    assert not tasks_dir.exists()
    assert not status_file.exists()


def test_reset__without_task_specs_flag__preserves_task_specs(tmp_path: Path) -> None:
    # given
    notepad = tmp_path / "notepad.md"
    notepad.write_text("test")

    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "plan.yaml").write_text("test")
    status_file = sisyphus_dir / "status.json"
    status_file.write_text("{}")

    # when
    result = runner.invoke(reset_app, ["--cwd", str(tmp_path), "--yes"])

    # then
    assert result.exit_code == 0
    assert not notepad.exists()
    assert tasks_dir.exists()
    assert status_file.exists()


def test_reset__with_dry_run__does_not_delete(tmp_path: Path) -> None:
    # given
    notepad = tmp_path / "notepad.md"
    notepad.write_text("test")

    # when
    result = runner.invoke(reset_app, ["--cwd", str(tmp_path), "--dry-run"])

    # then
    assert result.exit_code == 0
    assert "Dry run mode - nothing was deleted" in result.stdout
    assert notepad.exists()


def test_reset__with_dry_run__shows_what_would_be_deleted(tmp_path: Path) -> None:
    # given
    notepad = tmp_path / "notepad.md"
    sessions = tmp_path / "sessions"
    notepad.write_text("test")
    sessions.mkdir()

    # when
    result = runner.invoke(reset_app, ["--cwd", str(tmp_path), "--dry-run"])

    # then
    assert result.exit_code == 0
    assert "notepad.md" in result.stdout
    assert "sessions" in result.stdout
    assert "The following will be deleted:" in result.stdout


def test_reset__without_yes_flag__prompts_confirmation(tmp_path: Path) -> None:
    # given
    notepad = tmp_path / "notepad.md"
    notepad.write_text("test")

    # when: user cancels
    result = runner.invoke(reset_app, ["--cwd", str(tmp_path)], input="n\n")

    # then
    assert result.exit_code == 0
    assert "Operation cancelled" in result.stdout
    assert notepad.exists()


def test_reset__with_yes_flag__skips_confirmation(tmp_path: Path) -> None:
    # given
    notepad = tmp_path / "notepad.md"
    notepad.write_text("test")

    # when
    result = runner.invoke(reset_app, ["--cwd", str(tmp_path), "--yes"])

    # then
    assert result.exit_code == 0
    assert "Operation cancelled" not in result.stdout
    assert not notepad.exists()
