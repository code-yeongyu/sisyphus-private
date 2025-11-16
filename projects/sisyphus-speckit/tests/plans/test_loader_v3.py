from pathlib import Path

import pytest
from sisyphus_core.core.plans.loader import load_plan
from sisyphus_core.core.plans.models import PlanDocument

pytestmark = [pytest.mark.anyio]


async def test_load_plan__if_v3_file__loads_successfully(tmp_path: Path) -> None:
    """v3.0 YAML 파일을 정상적으로 로딩"""
    # given
    plan_file = tmp_path / "test_v3.yaml"
    plan_file.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T20:00:00Z"
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
        title: "Test Task"
        status: pending
""")

    # when
    result = await load_plan(plan_file)

    # then
    assert isinstance(result, PlanDocument)
    assert result.version == "3.0"
    assert len(result.work_plans) == 1
    assert result.work_plans[0].id == "plan-test"


async def test_load_plan__if_v2_1_file__raises_value_error(tmp_path: Path) -> None:
    """v2.1 YAML 파일은 ValueError 발생"""
    # given
    plan_file = tmp_path / "test_v2.yaml"
    plan_file.write_text("""version: "2.1"
metadata:
  created_at: "2025-11-01T20:00:00Z"
work_plan:
  name: "Test Plan"
  todos: []
""")

    # when & then
    with pytest.raises(ValueError, match="Unsupported version.*2\\.1.*Only v3\\.0 supported"):
        await load_plan(plan_file)


async def test_load_plan__if_v2_0_file__raises_value_error(tmp_path: Path) -> None:
    """v2.0 YAML 파일도 ValueError 발생"""
    # given
    plan_file = tmp_path / "test_v2_0.yaml"
    plan_file.write_text("""version: "2.0"
metadata:
  created_at: "2025-11-01T20:00:00Z"
work_plan:
  name: "Test Plan"
  todos: []
""")

    # when & then
    with pytest.raises(ValueError, match="Unsupported version.*2\\.0.*Only v3\\.0 supported"):
        await load_plan(plan_file)


async def test_load_plan__if_missing_version__raises_value_error(tmp_path: Path) -> None:
    """version 필드가 없으면 ValueError 발생"""
    # given
    plan_file = tmp_path / "test_no_version.yaml"
    plan_file.write_text("""metadata:
  created_at: "2025-11-01T20:00:00Z"
work_plans: []
""")

    # when & then
    with pytest.raises(ValueError, match="missing 'version' field"):
        await load_plan(plan_file)


async def test_load_plan__if_unknown_version__raises_value_error(tmp_path: Path) -> None:
    """알 수 없는 버전은 ValueError 발생"""
    # given
    plan_file = tmp_path / "test_unknown.yaml"
    plan_file.write_text("""version: "99.9"
metadata:
  created_at: "2025-11-01T20:00:00Z"
work_plans: []
""")

    # when & then
    with pytest.raises(ValueError, match="Unsupported version.*99\\.9.*Only v3\\.0 supported"):
        await load_plan(plan_file)


async def test_load_plan__if_file_not_found__raises_file_not_found_error(tmp_path: Path) -> None:
    """존재하지 않는 파일은 FileNotFoundError 발생"""
    # given
    plan_file = tmp_path / "nonexistent.yaml"

    # when & then
    with pytest.raises(FileNotFoundError):
        await load_plan(plan_file)


async def test_load_plan__if_v3_with_depends_on__loads_successfully(tmp_path: Path) -> None:
    """v3.0 depends_on 필드가 있는 파일 로딩"""
    # given
    plan_file = tmp_path / "test_v3_deps.yaml"
    plan_file.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-01T20:00:00Z"
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
      - plan-setup
    todos:
      - id: "1"
        title: "Task"
        description: "Task description"
        status: pending
""")

    # when
    result = await load_plan(plan_file)

    # then
    assert result.work_plans[0].depends_on == ["plan-foundation", "plan-setup"]
    assert result.work_plans[0].todos[0].description == "Task description"
