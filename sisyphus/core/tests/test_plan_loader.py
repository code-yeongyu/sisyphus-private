from pathlib import Path

import pytest
from pydantic import ValidationError
from ruamel.yaml import YAMLError

from sisyphus.core.plan_loader import PlanLoader
from sisyphus.utils.plan_types import (
    Background,
    CommandInput,
    ExecutionStatus,
    Metadata,
    NoneVerify,
    Objectives,
    Progress,
    RequiredBackground,
    Status,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    VerificationItem,
    Workflow,
    WorkMode,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


async def test_load_valid_yaml(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """metadata:
  created_at: "2025-10-28T14:32:15+09:00"
  updated_at: "2025-10-28T14:32:15+09:00"
user_request:
  original: "Test"
  timestamp: "2025-10-28"
objectives:
  core: "Test objective"
  detailed: []
background:
  current_situation: "A"
  reason_for_change: "B"
  changes_to_make: "C"
required_background:
  description: "Test background"
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: null
  progress:
    total_tasks: 0
    completed: 0
    in_progress: 0
    pending: 0
  current_work: "None"
workflow:
  dependency_diagram: "Test"
todos: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content, encoding="utf-8")

    # when
    loader = PlanLoader(yaml_file)
    plan = loader.load()

    # then
    assert plan.objectives.core == "Test objective"
    assert plan.metadata.format_version == "2.0"


async def test_load_nonexistent_file() -> None:
    # given
    loader = PlanLoader(Path("nonexistent.yaml"))

    # when & then
    with pytest.raises(FileNotFoundError) as exc:
        loader.load()
    assert "작업계획서를 찾을 수 없습니다" in str(exc.value)


async def test_save_and_reload(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "test.yaml"
    loader = PlanLoader(yaml_file)

    plan = WorkPlan(
        metadata=Metadata(created_at="2025-01-01", updated_at="2025-01-01"),
        user_request=UserRequest(original="Test", timestamp="2025-01-01"),
        objectives=Objectives(core="Test"),
        background=Background(current_situation="A", reason_for_change="B", changes_to_make="C"),
        required_background=RequiredBackground(description="Test"),
        status=Status(
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id=None),
            progress=Progress(total_tasks=0, completed=0, in_progress=0, pending=0),
            current_work="None",
        ),
        workflow=Workflow(dependency_diagram="Test"),
        todos=[],
        success_vision=SuccessVision(),
        final_verification=[],
    )

    # when
    loader.save(plan)
    reloaded = loader.load()

    # then
    assert reloaded.objectives.core == "Test"
    assert reloaded.metadata.format_version == "2.0"


async def test_load_malformed_yaml__when_invalid_syntax__raises_yaml_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "malformed.yaml"
    malformed_content = """
metadata:
  created_at: "2025-01-01"
  invalid indentation here
    more_invalid: "value"
"""
    yaml_file.write_text(malformed_content, encoding="utf-8")

    # when & then
    loader = PlanLoader(yaml_file)
    with pytest.raises((YAMLError, ValidationError)):
        loader.load()


async def test_load_yaml_with_invalid_schema__when_wrong_types__raises_validation_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "invalid_schema.yaml"
    invalid_content = """
metadata:
  created_at: 12345
  updated_at: "2025-01-01"
user_request:
  original: "Test"
  timestamp: "2025-01-01"
objectives:
  core: "Test"
background:
  current_situation: "A"
  reason_for_change: "B"
  changes_to_make: "C"
required_background:
  description: "Test"
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: null
  progress:
    total_tasks: 0
    completed: 0
    in_progress: 0
    pending: 0
  current_work: "None"
workflow:
  dependency_diagram: "Test"
todos: []
success_vision: {}
final_verification: []
"""
    yaml_file.write_text(invalid_content, encoding="utf-8")

    # when & then
    loader = PlanLoader(yaml_file)
    with pytest.raises(ValidationError):
        loader.load()


async def test_save_and_reload_with_verification_completed__when_completed_field_set__persists_correctly(
    tmp_path: Path,
) -> None:
    # given

    yaml_file = tmp_path / "test.yaml"
    loader = PlanLoader(yaml_file)

    verification_completed = VerificationItem(
        id="v1",
        description="Test verification",
        input=CommandInput(type="command", command="pytest"),
        verify=NoneVerify(type="none"),
        completed=True,
    )
    verification_incomplete = VerificationItem(
        id="v2",
        description="Another test",
        input=CommandInput(type="command", command="ruff check"),
        verify=NoneVerify(type="none"),
        completed=False,
    )

    task = Todo(
        id="1",
        title="Test Task",
        status=TodoStatus.in_progress,
        created_at="2025-01-01",
        updated_at="2025-01-01",
        verification_spec=[verification_completed, verification_incomplete],
    )

    plan = WorkPlan(
        metadata=Metadata(created_at="2025-01-01", updated_at="2025-01-01"),
        user_request=UserRequest(original="Test", timestamp="2025-01-01"),
        objectives=Objectives(core="Test"),
        background=Background(current_situation="A", reason_for_change="B", changes_to_make="C"),
        required_background=RequiredBackground(description="Test"),
        status=Status(
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id=None),
            progress=Progress(total_tasks=0, completed=0, in_progress=0, pending=0),
            current_work="None",
        ),
        workflow=Workflow(dependency_diagram="Test"),
        todos=[task],
        success_vision=SuccessVision(),
        final_verification=[],
    )

    # when
    loader.save(plan)
    reloaded = loader.load()

    # then
    assert len(reloaded.todos) == 1
    assert len(reloaded.todos[0].verification_spec) == 2
    assert reloaded.todos[0].verification_spec[0].id == "v1"
    assert reloaded.todos[0].verification_spec[0].completed is True
    assert reloaded.todos[0].verification_spec[1].id == "v2"
    assert reloaded.todos[0].verification_spec[1].completed is False


async def test_save_and_reload_without_completed_field__when_old_yaml__defaults_to_false(tmp_path: Path) -> None:
    # given - YAML without completed field (backward compatibility)
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
user_request:
  original: "Test"
  timestamp: "2025-01-01"
objectives:
  core: "Test"
background:
  current_situation: "A"
  reason_for_change: "B"
  changes_to_make: "C"
required_background:
  description: "Test"
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: null
  progress:
    total_tasks: 0
    completed: 0
    in_progress: 0
    pending: 0
  current_work: "None"
workflow:
  dependency_diagram: "Test"
todos:
  - id: "1"
    title: "Task 1"
    status: "pending"
    created_at: "2025-01-01"
    updated_at: "2025-01-01"
    verification_spec:
      - id: "v1"
        description: "Test verification"
        input:
          type: "command"
          command: "pytest"
        verify:
          type: "none"
success_vision: {}
final_verification: []
"""
    yaml_file.write_text(yaml_content, encoding="utf-8")

    # when
    loader = PlanLoader(yaml_file)
    plan = loader.load()

    # then
    assert len(plan.todos[0].verification_spec) == 1
    assert plan.todos[0].verification_spec[0].completed is False
