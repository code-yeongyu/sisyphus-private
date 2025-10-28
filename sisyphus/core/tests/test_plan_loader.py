from pathlib import Path

import pytest

from sisyphus.core.plan_loader import PlanLoader
from sisyphus.utils.plan_types import (
    Background,
    ExecutionStatus,
    Metadata,
    Objectives,
    Progress,
    RequiredBackground,
    Status,
    SuccessVision,
    UserRequest,
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
