from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus_core.core.plans.loader import load_plan

pytestmark = [pytest.mark.anyio]


async def test_load_plan__if_valid_v3_yaml__loads_successfully(tmp_path: Path) -> None:
    # given
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T20:00:00Z"
work_plans:
  - id: plan-test
    name: "Test Plan"
    user_request:
      original: "Test request"
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
    todos: []
    acceptance_criteria_for_verification_agent:
      - id: "criteria-1"
        title: "Test verification criteria"
        checklists:
          - id: "check-1"
            title: "Functionality"
            content: "Core functionality works as expected"
          - id: "check-2"
            title: "Performance"
            content: "Performance meets minimum requirements"
          - id: "check-3"
            title: "Security"
            content: "Security requirements are met"
          - id: "check-4"
            title: "Quality"
            content: "Code quality standards are met"
"""
    plan_file = tmp_path / "test.yaml"
    _ = plan_file.write_text(yaml_content)

    # when
    result = await load_plan(plan_file)

    # then
    assert result.version == "3.0"
    assert len(result.work_plans) == 1
    assert result.work_plans[0].id == "plan-test"


async def test_load_plan__if_missing_version__raises_error(tmp_path: Path) -> None:
    # given
    yaml_content = """metadata:
  created_at: "2025-11-01T20:00:00Z"
work_plans: []
"""
    plan_file = tmp_path / "test.yaml"
    _ = plan_file.write_text(yaml_content)

    # when & then
    with pytest.raises(ValueError, match="missing 'version' field"):
        _ = await load_plan(plan_file)


async def test_load_plan__if_unsupported_version__raises_error(tmp_path: Path) -> None:
    # given
    yaml_content = """version: "2.1"
metadata:
  created_at: "2025-11-01T20:00:00Z"
work_plans: []
"""
    plan_file = tmp_path / "test.yaml"
    _ = plan_file.write_text(yaml_content)

    # when & then
    with pytest.raises(ValueError, match="Unsupported version.*2\\.1.*Only v3\\.0 supported"):
        _ = await load_plan(plan_file)


async def test_load_plan__if_file_not_found__raises_error(tmp_path: Path) -> None:
    # given
    plan_file = tmp_path / "nonexistent.yaml"

    # when & then
    with pytest.raises(FileNotFoundError):
        _ = await load_plan(plan_file)
