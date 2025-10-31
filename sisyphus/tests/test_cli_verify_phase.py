"""CLI verify-phase subcommand tests."""

from __future__ import annotations

from typer.testing import CliRunner

from sisyphus.cli import app

runner = CliRunner()


def test_verify_phase_help__shows_command_description() -> None:
    # given / when
    result = runner.invoke(app, ["verify-phase", "--help"])

    # then
    assert result.exit_code == 0
    assert "Verify phase commands" in result.stdout
    assert "Usage: sisyphus verify-phase" in result.stdout
