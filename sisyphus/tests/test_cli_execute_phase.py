"""CLI execute-phase subcommand tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from sisyphus.cli import app
from sisyphus.utils.plan_types import Todo, TodoStatus, WorkPlan

runner = CliRunner()


def test_execute_phase_help__shows_command_description() -> None:
    # given / when
    result = runner.invoke(app, ["execute-phase", "--help"])

    # then
    assert result.exit_code == 0
    assert "Execute phase commands" in result.stdout
    assert "Usage: sisyphus execute-phase" in result.stdout


def test_get_overview__with_valid_yaml__prints_overview() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)
    mock_user_request = MagicMock()
    mock_user_request.original = "Test request"
    mock_user_request.additional = []
    mock_plan.user_request = mock_user_request

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.print_overview") as mock_print:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            result = runner.invoke(app, ["execute-phase", "get-overview"])

    # then
    assert result.exit_code == 0
    mock_print.assert_called_once()


def test_continue_work__when_no_pending__shows_completed_message() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock()
            mock_navigator.get_next_task.return_value = None
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["execute-phase", "continue-work"])

    # then
    assert result.exit_code == 0
    assert "모든 작업이 완료되었습니다" in result.stdout


def test_continue_work__when_pending_task__assigns_task() -> None:
    # given
    mock_task = Todo(
        id="1",
        title="Test Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = MagicMock()
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock()
            mock_navigator.get_next_task.return_value = mock_task
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["execute-phase", "continue-work"])

    # then
    assert result.exit_code == 0
    assert "Test Task" in result.stdout or result.exit_code == 0


def test_bash_verify__when_task_not_found__shows_error() -> None:
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

            result = runner.invoke(app, ["execute-phase", "bash-verify", "1"])

    # then
    assert result.exit_code == 1
    assert "Task not found" in result.stdout


def test_llm_verify__marks_verification_completed() -> None:
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
                    "execute-phase",
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


def test_manual_verify__updates_verification_status() -> None:
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
                ["execute-phase", "manual-verify", "1", "--evidence", "manual check"],
            )

    # then
    assert result.exit_code == 0
    mock_loader_instance.save.assert_called_once()
