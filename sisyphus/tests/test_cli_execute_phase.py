"""CLI execute-phase subcommand tests."""

from __future__ import annotations

from typer.testing import CliRunner

from sisyphus.cli import app

runner = CliRunner()


def test_execute_phase_help__shows_command_description() -> None:
    # given / when
    result = runner.invoke(app, ["execute-phase", "--help"])

    # then
    assert result.exit_code == 0
    assert "Execute phase commands" in result.stdout
    assert "Usage: sisyphus execute-phase" in result.stdout
