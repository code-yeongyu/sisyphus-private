"""Tests for root CLI structure after refactoring."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from sisyphus_core.cli import app

pytestmark = [pytest.mark.anyio]

runner = CliRunner()


async def test_cli_help__shows_main_commands__displays_work_ignore_clean_history() -> None:
    # given: CLI app
    # when: running --help
    result = runner.invoke(app, ["--help"])

    # then: shows work, ignore, clean-history commands
    assert result.exit_code == 0
    assert "work" in result.stdout
    assert "ignore" in result.stdout
    assert "clean-history" in result.stdout


async def test_cli_help__shows_new_command_groups__displays_plan_task_reset() -> None:
    # given: CLI app
    # when: running --help
    result = runner.invoke(app, ["--help"])

    # then: shows plan, task, reset command groups
    assert result.exit_code == 0
    assert "plan" in result.stdout
    assert "task" in result.stdout
    assert "reset" in result.stdout


async def test_cli_help__deprecated_commands_removed__no_execute_phase_verify_phase() -> None:
    # given: CLI app
    # when: running --help
    result = runner.invoke(app, ["--help"])

    # then: execute-phase and verify-phase are not present
    assert result.exit_code == 0
    assert "execute-phase" not in result.stdout
    assert "verify-phase" not in result.stdout


async def test_plan_command__exists__shows_help() -> None:
    # given: CLI app
    # when: running plan --help
    result = runner.invoke(app, ["plan", "--help"])

    # then: shows plan subcommands
    assert result.exit_code == 0
    assert "lint" in result.stdout or "overview" in result.stdout


async def test_task_command__exists__shows_help() -> None:
    # given: CLI app
    # when: running task --help
    result = runner.invoke(app, ["task", "--help"])

    # then: shows task subcommands
    assert result.exit_code == 0
    assert "show" in result.stdout or "current" in result.stdout or "next" in result.stdout


async def test_reset_command__exists__shows_help() -> None:
    # given: CLI app
    # when: running reset --help
    result = runner.invoke(app, ["reset", "--help"])

    # then: shows reset options
    assert result.exit_code == 0
    assert "Reset" in result.stdout or "reset" in result.stdout


async def test_execute_phase_command__removed__returns_error() -> None:
    # given: CLI app
    # when: running execute-phase (deprecated command)
    result = runner.invoke(app, ["execute-phase", "--help"])

    # then: command not found
    assert result.exit_code != 0


async def test_verify_phase_command__removed__returns_error() -> None:
    # given: CLI app
    # when: running verify-phase (deprecated command)
    result = runner.invoke(app, ["verify-phase", "--help"])

    # then: command not found
    assert result.exit_code != 0
