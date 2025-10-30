"""CLI plan subcommand tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from sisyphus.cli import app
from sisyphus.core.plan_navigator import CompletionReport, PlanNavigator
from sisyphus.utils.formatting import OutputFormat
from sisyphus.utils.plan_types import (
    CommandInput,
    NoneVerify,
    SimpleReference,
    Todo,
    TodoStatus,
    VerificationItem,
    WorkPlan,
)

runner = CliRunner()


def test_plan_get_task_current__when_not_started__shows_message() -> None:
    # given
    mock_plan = MagicMock()
    mock_work_mode = MagicMock()
    mock_work_mode.current_task_id = None
    mock_status = MagicMock()
    mock_status.work_mode = mock_work_mode
    mock_plan.status = mock_status

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = mock_plan
        mock_loader.return_value = mock_loader_instance

        result = runner.invoke(app, ["plan", "get", "task", "--current"])

    # then
    assert result.exit_code == 0
    assert "작업이 시작되지 않았습니다" in result.stdout


def test_plan_get_task_next__when_no_pending__shows_completed_message() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)
    mock_plan.todos = []

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator.get_next_task.return_value = None
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "get", "task", "--next"])

    # then
    assert result.exit_code == 0
    assert "모든 작업이 완료되었습니다" in result.stdout


def test_plan_get_task_id__when_task_exists__prints_task() -> None:
    # given
    mock_task = Todo(
        id="1.1",
        title="Test Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            with patch("sisyphus.cli.print_task") as mock_print_task:
                mock_loader_instance = MagicMock()
                mock_loader_instance.load.return_value = mock_plan
                mock_loader.return_value = mock_loader_instance

                mock_navigator = MagicMock(spec=PlanNavigator)
                mock_navigator.find_todo_by_id.return_value = mock_task
                mock_navigator_class.return_value = mock_navigator

                result = runner.invoke(app, ["plan", "get", "task", "--id", "1.1"])

    # then
    assert result.exit_code == 0
    mock_print_task.assert_called_once_with(mock_task, format=OutputFormat.PLAIN)


def test_plan_get_task_id__when_task_not_found__shows_error() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator.find_todo_by_id.return_value = None
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "get", "task", "--id", "999"])

    # then
    assert result.exit_code == 1
    assert "작업 ID를 찾을 수 없습니다" in result.stdout


def test_plan_get_task__when_no_option_provided__shows_error() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "get", "task"])

    # then
    assert result.exit_code == 1
    assert "--current, --next, --id 중 하나를 선택하세요" in result.stdout


def test_plan_get_reference__shows_not_implemented() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "get", "reference"])

    # then
    assert result.exit_code == 1
    assert "Reference lookup not yet implemented" in result.stdout


def test_plan_set_current_task__when_valid_id__updates_plan() -> None:
    # given
    mock_plan = MagicMock()
    mock_work_mode = MagicMock()
    mock_work_mode.current_task_id = None
    mock_status = MagicMock()
    mock_status.work_mode = mock_work_mode
    mock_plan.status = mock_status

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = mock_plan
        mock_loader.return_value = mock_loader_instance

        result = runner.invoke(app, ["plan", "set", "current-task", "1.1"])

    # then
    assert result.exit_code == 0
    assert "Current task set to: 1.1" in result.stdout
    assert mock_plan.status.work_mode.current_task_id == "1.1"
    mock_loader_instance.save.assert_called_once_with(mock_plan)


def test_plan_set_task_status__when_no_status_option__shows_error() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = mock_plan
        mock_loader.return_value = mock_loader_instance

        result = runner.invoke(app, ["plan", "set", "task-status", "1.1"])

    # then
    assert result.exit_code == 1
    assert "--status 옵션이 필요합니다" in result.stdout


def test_plan_set_task_status__when_task_not_found__shows_error() -> None:
    # given
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator.find_todo_by_id.return_value = None
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "set", "task-status", "999", "--status", "completed"])

    # then
    assert result.exit_code == 1
    assert "작업 ID를 찾을 수 없습니다" in result.stdout


def test_plan_set_task_status__when_valid__updates_status() -> None:
    # given
    mock_task = Todo(
        id="1.1", title="Test Task", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"
    )
    mock_plan = MagicMock(spec=WorkPlan)
    mock_plan.todos = [mock_task]

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator.find_todo_by_id.return_value = mock_task
            mock_navigator.get_all_descendants.return_value = []
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "set", "task-status", "1.1", "--status", "completed"])

    # then
    assert result.exit_code == 0
    assert "1개 태스크 상태 변경" in result.stdout
    mock_loader_instance.save.assert_called_once()


def test_plan_get__when_file_not_found__shows_error() -> None:
    # given / when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.side_effect = FileNotFoundError("작업계획서를 찾을 수 없습니다")
        mock_loader.return_value = mock_loader_instance

        result = runner.invoke(app, ["plan", "get", "task", "--current"])

    # then
    assert result.exit_code == 1
    assert "작업계획서를 찾을 수 없습니다" in result.stdout


def test_plan_set__when_file_not_found__shows_error() -> None:
    # given / when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.side_effect = FileNotFoundError("작업계획서를 찾을 수 없습니다")
        mock_loader.return_value = mock_loader_instance

        result = runner.invoke(app, ["plan", "set", "current-task", "1.1"])

    # then
    assert result.exit_code == 1
    assert "작업계획서를 찾을 수 없습니다" in result.stdout


def test_plan_get_task_show_references__when_task_has_references__prints_references() -> None:
    # given

    mock_task = Todo(
        id="1",
        title="Test Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )
    mock_refs = [
        SimpleReference(ref_id="ref-1", note="First reference"),
        SimpleReference(ref_id="ref-2", note="Second reference"),
    ]
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            with patch("sisyphus.cli.print_references") as mock_print_references:
                mock_loader_instance = MagicMock()
                mock_loader_instance.load.return_value = mock_plan
                mock_loader.return_value = mock_loader_instance

                mock_navigator = MagicMock(spec=PlanNavigator)
                mock_navigator.find_todo_by_id.return_value = mock_task
                mock_navigator.get_task_references.return_value = mock_refs
                mock_navigator_class.return_value = mock_navigator

                result = runner.invoke(app, ["plan", "get", "task", "--id", "1", "--show-references"])

    # then
    assert result.exit_code == 0
    mock_navigator.get_task_references.assert_called_once_with("1")
    mock_print_references.assert_called_once_with(mock_refs, format=OutputFormat.PLAIN)


def test_plan_get_task_show_children__when_task_has_children__prints_children() -> None:
    # given
    mock_task = Todo(
        id="1",
        title="Parent Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )
    mock_children = [
        Todo(id="1.1", title="Child 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
        Todo(id="1.2", title="Child 2", status=TodoStatus.completed, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            with patch("sisyphus.cli.print_children") as mock_print_children:
                mock_loader_instance = MagicMock()
                mock_loader_instance.load.return_value = mock_plan
                mock_loader.return_value = mock_loader_instance

                mock_navigator = MagicMock(spec=PlanNavigator)
                mock_navigator.find_todo_by_id.return_value = mock_task
                mock_navigator.get_task_children.return_value = mock_children
                mock_navigator_class.return_value = mock_navigator

                result = runner.invoke(app, ["plan", "get", "task", "--id", "1", "--show-children"])

    # then
    assert result.exit_code == 0
    mock_navigator.get_task_children.assert_called_once_with("1")
    mock_print_children.assert_called_once_with(mock_children, format=OutputFormat.PLAIN)


def test_plan_get_task_show_verification__when_task_has_verification__prints_verification() -> None:
    # given

    mock_task = Todo(
        id="1",
        title="Test Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )
    mock_verifications = [
        VerificationItem(
            id="v1",
            description="Verify tests pass",
            input=CommandInput(type="command", command="pytest"),
            verify=NoneVerify(type="none"),
            completed=False,
        ),
        VerificationItem(
            id="v2",
            description="Verify lint passes",
            input=CommandInput(type="command", command="ruff check"),
            verify=NoneVerify(type="none"),
            completed=True,
        ),
    ]
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            with patch("sisyphus.cli.print_verification") as mock_print_verification:
                mock_loader_instance = MagicMock()
                mock_loader_instance.load.return_value = mock_plan
                mock_loader.return_value = mock_loader_instance

                mock_navigator = MagicMock(spec=PlanNavigator)
                mock_navigator.find_todo_by_id.return_value = mock_task
                mock_navigator.get_task_verification.return_value = mock_verifications
                mock_navigator_class.return_value = mock_navigator

                result = runner.invoke(app, ["plan", "get", "task", "--id", "1", "--show-verification"])

    # then
    assert result.exit_code == 0
    mock_navigator.get_task_verification.assert_called_once_with("1")
    mock_print_verification.assert_called_once_with(mock_verifications, format=OutputFormat.PLAIN)


def test_plan_get_task__when_no_filter_specified__prints_full_task() -> None:
    # given
    mock_task = Todo(
        id="1",
        title="Test Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            with patch("sisyphus.cli.print_task") as mock_print_task:
                mock_loader_instance = MagicMock()
                mock_loader_instance.load.return_value = mock_plan
                mock_loader.return_value = mock_loader_instance

                mock_navigator = MagicMock(spec=PlanNavigator)
                mock_navigator.find_todo_by_id.return_value = mock_task
                mock_navigator_class.return_value = mock_navigator

                result = runner.invoke(app, ["plan", "get", "task", "--id", "1"])

    # then
    assert result.exit_code == 0
    mock_print_task.assert_called_once_with(mock_task, format=OutputFormat.PLAIN)


def test_plan_set_task_status_recursive__when_task_has_children__updates_all() -> None:
    # given
    child1 = Todo(
        id="1.1", title="Child 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"
    )
    child2 = Todo(
        id="1.2", title="Child 2", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"
    )
    parent = Todo(
        id="1",
        title="Parent",
        status=TodoStatus.in_progress,
        created_at="2025-01-01",
        updated_at="2025-01-01",
        children=[child1, child2],
    )
    mock_plan = MagicMock(spec=WorkPlan)
    mock_plan.todos = [parent]

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator.find_todo_by_id.return_value = parent
            mock_navigator.get_all_descendants.return_value = [child1, child2]
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "set", "task-status", "1", "--status", "completed", "--recursive"])

    # then
    assert result.exit_code == 0
    assert "3개 태스크 상태 변경" in result.stdout
    mock_loader_instance.save.assert_called_once()


def test_plan_set_verification__when_verification_exists__updates_status() -> None:
    # given
    verification = VerificationItem(
        id="v1",
        description="Test verification",
        input=CommandInput(type="command", command="pytest"),
        verify=NoneVerify(type="none"),
        completed=False,
    )
    mock_task = Todo(
        id="1",
        title="Test Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
        verification_spec=[verification],
    )
    mock_plan = MagicMock(spec=WorkPlan)
    mock_plan.todos = [mock_task]

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator.find_todo_by_id.return_value = mock_task
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "set-verification", "1", "v1", "--completed"])

    # then
    assert result.exit_code == 0
    assert "완료" in result.stdout
    mock_loader_instance.save.assert_called_once()


def test_plan_set_verification__when_verification_not_found__shows_error() -> None:
    # given
    mock_task = Todo(
        id="1", title="Test Task", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"
    )
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = mock_plan
            mock_loader.return_value = mock_loader_instance

            mock_navigator = MagicMock(spec=PlanNavigator)
            mock_navigator.find_todo_by_id.return_value = mock_task
            mock_navigator_class.return_value = mock_navigator

            result = runner.invoke(app, ["plan", "set-verification", "1", "nonexistent", "--completed"])

    # then
    assert result.exit_code == 1
    assert "검증 ID를 찾을 수 없습니다" in result.stdout


def test_plan_check__when_task_exists__prints_report() -> None:
    # given

    mock_report = CompletionReport(
        task_id="1",
        task_status=TodoStatus.in_progress,
        all_children_completed=False,
        children_summary={"completed": 1, "in_progress": 1, "pending": 0},
        all_verifications_completed=True,
        verification_summary={"completed": 2, "total": 2},
        can_complete=False,
    )
    mock_plan = MagicMock(spec=WorkPlan)

    # when
    with patch("sisyphus.cli.PlanLoader") as mock_loader:
        with patch("sisyphus.cli.PlanNavigator") as mock_navigator_class:
            with patch("sisyphus.cli.print_completion_report") as mock_print_report:
                mock_loader_instance = MagicMock()
                mock_loader_instance.load.return_value = mock_plan
                mock_loader.return_value = mock_loader_instance

                mock_navigator = MagicMock(spec=PlanNavigator)
                mock_navigator.check_task_completion.return_value = mock_report
                mock_navigator_class.return_value = mock_navigator

                result = runner.invoke(app, ["plan", "check", "1"])

    # then
    assert result.exit_code == 0
    mock_navigator.check_task_completion.assert_called_once_with("1")
    mock_print_report.assert_called_once_with(mock_report, format=OutputFormat.PLAIN)
