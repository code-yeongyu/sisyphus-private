from pathlib import Path

import pytest

from sisyphus_core.core.plans.loader import load_multiple_plans, resolve_current_plan_from_status
from sisyphus_core.core.plans.models import PlanDocument

pytestmark = [pytest.mark.anyio]


async def test_load_multiple_plans__if_empty_directory__returns_empty_dict(tmp_path: Path) -> None:
    # given
    root = tmp_path
    tasks_dir = root / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    # when
    result = await load_multiple_plans(root)

    # then
    assert result == {}


async def test_load_multiple_plans__if_no_tasks_directory__returns_empty_dict(tmp_path: Path) -> None:
    # given
    root = tmp_path

    # when
    result = await load_multiple_plans(root)

    # then
    assert result == {}


async def test_load_multiple_plans__if_single_plan__returns_one_item_dict(tmp_path: Path) -> None:
    # given
    root = tmp_path
    tasks_dir = root / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    plan_file = tasks_dir / "test.yaml"
    plan_file.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plans:
  - id: plan-test
    name: "Test Plan"
    user_request:
      original: "Test user request"
      created_at: "2025-11-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test objective"
      detailed: []
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test diagram"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    depends_on: []
    todos:
      - id: "1"
        title: "Task 1"
        status: pending
""")

    # when
    result = await load_multiple_plans(root)

    # then
    assert len(result) == 1
    assert "plan-test" in result
    assert isinstance(result["plan-test"], PlanDocument)
    assert result["plan-test"].work_plans[0].name == "Test Plan"


async def test_load_multiple_plans__if_multiple_plans__returns_n_item_dict(tmp_path: Path) -> None:
    # given
    root = tmp_path
    tasks_dir = root / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    plan1 = tasks_dir / "foundation.yaml"
    plan1.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plans:
  - id: plan-foundation
    name: "Foundation Plan"
    user_request:
      original: "Test user request"
      created_at: "2025-11-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test objective"
      detailed: []
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test diagram"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    depends_on: []
    todos:
      - id: "1"
        title: "Setup"
        status: pending
""")

    plan2 = tasks_dir / "main.yaml"
    plan2.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plans:
  - id: plan-main
    name: "Main Plan"
    user_request:
      original: "Test user request"
      created_at: "2025-11-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test objective"
      detailed: []
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test diagram"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    depends_on:
      - plan-foundation
    todos:
      - id: "1"
        title: "Feature"
        status: pending
""")

    plan3 = tasks_dir / "cleanup.yaml"
    plan3.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plans:
  - id: plan-cleanup
    name: "Cleanup Plan"
    user_request:
      original: "Test user request"
      created_at: "2025-11-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test objective"
      detailed: []
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test diagram"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    depends_on:
      - plan-main
    todos:
      - id: "1"
        title: "Cleanup"
        status: pending
""")

    # when
    result = await load_multiple_plans(root)

    # then
    assert len(result) == 3
    assert "plan-foundation" in result
    assert "plan-main" in result
    assert "plan-cleanup" in result
    assert result["plan-main"].work_plans[0].depends_on == ["plan-foundation"]
    assert result["plan-cleanup"].work_plans[0].depends_on == ["plan-main"]


async def test_load_multiple_plans__if_v2_1_file__raises_value_error_with_details(tmp_path: Path) -> None:
    # given
    root = tmp_path
    tasks_dir = root / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    legacy_file = tasks_dir / "legacy.yaml"
    legacy_file.write_text("""version: "2.1"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plan:
  name: "Legacy Plan"
  todos: []
""")

    # when & then
    with pytest.raises(ValueError, match="Failed to load some plans"):
        await load_multiple_plans(root)


async def test_load_multiple_plans__if_subdirectory_plans__loads_all(tmp_path: Path) -> None:
    # given
    root = tmp_path
    tasks_dir = root / ".sisyphus" / "tasks"
    subdir = tasks_dir / "archived"
    subdir.mkdir(parents=True)

    plan1 = tasks_dir / "active.yaml"
    plan1.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plans:
  - id: plan-active
    name: "Active Plan"
    user_request:
      original: "Test user request"
      created_at: "2025-11-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test objective"
      detailed: []
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test diagram"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    depends_on: []
    todos:
      - id: "1"
        title: "Task"
        status: pending
""")

    plan2 = subdir / "archived.yaml"
    plan2.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plans:
  - id: plan-archived
    name: "Archived Plan"
    user_request:
      original: "Test user request"
      created_at: "2025-11-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test objective"
      detailed: []
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test diagram"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    depends_on: []
    todos:
      - id: "1"
        title: "Task"
        status: completed
""")

    # when
    result = await load_multiple_plans(root)

    # then
    assert len(result) == 2
    assert "plan-active" in result
    assert "plan-archived" in result


async def test_resolve_current_plan_from_status__if_no_status_json__returns_none(tmp_path: Path) -> None:
    # given
    root = tmp_path

    # when
    result = await resolve_current_plan_from_status(root)

    # then
    assert result is None


async def test_resolve_current_plan_from_status__if_current_plan_none__returns_none(tmp_path: Path) -> None:
    # given
    root = tmp_path
    status_file = root / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True)
    status_file.write_text('{"version": 1, "current_plan": null}')

    # when
    result = await resolve_current_plan_from_status(root)

    # then
    assert result is None


async def test_resolve_current_plan_from_status__if_valid_current_plan__returns_plan_document(tmp_path: Path) -> None:
    # given
    root = tmp_path
    tasks_dir = root / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    plan_file = tasks_dir / "current.yaml"
    plan_file.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plans:
  - id: plan-current
    name: "Current Plan"
    user_request:
      original: "Test user request"
      created_at: "2025-11-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test objective"
      detailed: []
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test diagram"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    depends_on: []
    todos:
      - id: "1"
        title: "Active Task"
        status: in_progress
""")

    status_file = root / ".sisyphus" / "status.json"
    status_file.write_text("""{
  "version": 1,
  "current_plan": {
    "plan_path": ".sisyphus/tasks/current.yaml",
    "plan_root": ".sisyphus/tasks/",
    "updated_at": "2025-11-01T21:00:00Z"
  }
}""")

    # when
    result = await resolve_current_plan_from_status(root)

    # then
    assert result is not None
    assert isinstance(result, PlanDocument)
    assert result.work_plans[0].id == "plan-current"
    assert result.work_plans[0].name == "Current Plan"


async def test_resolve_current_plan_from_status__if_missing_file__raises_file_not_found_error(tmp_path: Path) -> None:
    # given
    root = tmp_path
    status_file = root / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True)
    status_file.write_text("""{
  "version": 1,
  "current_plan": {
    "plan_path": ".sisyphus/tasks/missing.yaml",
    "plan_root": ".sisyphus/tasks/",
    "updated_at": "2025-11-01T21:00:00Z"
  }
}""")

    # when & then
    with pytest.raises(FileNotFoundError):
        await resolve_current_plan_from_status(root)


async def test_resolve_current_plan_from_status__if_v2_1_plan__raises_unsupported_error(tmp_path: Path) -> None:
    # given
    root = tmp_path
    tasks_dir = root / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    plan_file = tasks_dir / "legacy.yaml"
    plan_file.write_text("""version: "2.1"
metadata:
  created_at: "2025-11-01T21:00:00Z"
work_plan:
  name: "Legacy Plan"
  todos: []
""")

    status_file = root / ".sisyphus" / "status.json"
    status_file.write_text("""{
  "version": 1,
  "current_plan": {
    "plan_path": ".sisyphus/tasks/legacy.yaml",
    "plan_root": ".sisyphus/tasks/",
    "updated_at": "2025-11-01T21:00:00Z"
  }
}""")

    # when & then
    with pytest.raises(ValueError, match="Unsupported version.*2\\.1.*Only v3\\.0 supported"):
        await resolve_current_plan_from_status(root)
