"""CLI verify-phase subcommand tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from sisyphus.cli import app
from sisyphus.utils.plan_types import Todo, TodoStatus, WorkPlan

runner = CliRunner()


def test_verify_phase_help__shows_command_description() -> None:
    # given / when
    result = runner.invoke(app, ["verify-phase", "--help"])

    # then
    assert result.exit_code == 0
    assert "Verify phase commands" in result.stdout
    assert "Usage: sisyphus verify-phase" in result.stdout


def test_verify_phase_bash_verify__when_task_not_found__shows_error() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock()
            mock_navigator.find_todo_by_id.return_value = None
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["verify-phase", "bash-verify", "1"])

    # then
    assert result.exit_code == 1
    assert "Task not found" in result.stdout


def test_verify_phase_llm_verify__marks_verification_completed() -> None:
    # given
    mock_task = Todo(
        id="1",
        title="Test Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )
    mock_plan = MagicMock(spec=WorkPlan)
    mock_plan.todos = []

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock()
            mock_navigator.find_todo_by_id.return_value = mock_task
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(
                app,
                [
                    "verify-phase",
                    "llm-verify",
                    "1",
                    "--verify-id",
                    "v1",
                    "--evidence",
                    "test evidence",
                ],
            )

    # then
    assert result.exit_code == 0
    mock_loader_instance.save.assert_called_once()
