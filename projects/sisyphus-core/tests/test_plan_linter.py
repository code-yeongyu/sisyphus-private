from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from sisyphus_core.core.plan_linter import PlanLinter
from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaChecklist,
    AcceptanceCriteriaForVerificationAgent,
    Background,
    Metadata,
    Objectives,
    PlanDocument,
    RequiredBackground,
    SuccessVision,
    Todo,
    UserRequest,
    Workflow,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


def create_test_plan(plan_id: str, todos: list[Todo], depends_on: list[str] | None = None) -> PlanDocument:
    # Create acceptance criteria for verification agent (now required with 4 minimum)
    checklists = [
        AcceptanceCriteriaChecklist(
            id="check-1",
            title="Test functionality",
            content="Core functionality works as expected",
        ),
        AcceptanceCriteriaChecklist(
            id="check-2",
            title="Test performance",
            content="Performance meets minimum requirements",
        ),
        AcceptanceCriteriaChecklist(
            id="check-3",
            title="Test security",
            content="Security requirements are met",
        ),
        AcceptanceCriteriaChecklist(
            id="check-4",
            title="Test quality",
            content="Code quality standards are met",
        ),
    ]
    criteria = AcceptanceCriteriaForVerificationAgent(
        id="criteria-1",
        title="Test verification criteria",
        checklists=checklists,
    )

    return PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id=plan_id,
                name="Test Plan",
                user_request=UserRequest(original="Test", created_at="2025-11-06T00:00:00Z", additional=[]),
                objectives=Objectives(core="Test", detailed=[]),
                background=Background(current_situation="Test", reason_for_change="Test", changes_to_make="Test"),
                required_background=RequiredBackground(description="Test", file_structure=None, references=[]),
                workflow=Workflow(dependency_diagram="Test", critical_path=[]),
                success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
                final_verification=[],
                todos=todos,
                depends_on=depends_on or [],
                acceptance_criteria_for_verification_agent=[criteria],
            )
        ],
    )


async def test_plan_linter__if_valid_yaml__returns_no_errors() -> None:
    # given
    yaml_data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-11-06T00:00:00Z"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "user_request": {"original": "Test", "created_at": "2025-11-06T00:00:00Z", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "Test",
                    "reason_for_change": "Test",
                    "changes_to_make": "Test",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [{"id": "1", "title": "Task", "status": "pending"}],
                "acceptance_criteria_for_verification_agent": [
                    {
                        "id": "criteria-1",
                        "title": "Test verification criteria",
                        "checklists": [
                            {"id": "check-1", "title": "Functionality", "content": "Core functionality works"},
                            {"id": "check-2", "title": "Performance", "content": "Performance meets requirements"},
                        ],
                    },
                    {
                        "id": "criteria-2",
                        "title": "Security verification criteria",
                        "checklists": [
                            {"id": "check-3", "title": "Security", "content": "Security requirements met"},
                            {"id": "check-4", "title": "Authentication", "content": "Authentication works properly"},
                        ],
                    },
                    {
                        "id": "criteria-3",
                        "title": "Quality verification criteria",
                        "checklists": [
                            {"id": "check-5", "title": "Code quality", "content": "Code quality standards met"},
                            {"id": "check-6", "title": "Testing", "content": "Tests pass"},
                        ],
                    },
                    {
                        "id": "criteria-4",
                        "title": "Documentation verification criteria",
                        "checklists": [
                            {"id": "check-7", "title": "Documentation", "content": "Documentation is complete"},
                            {"id": "check-8", "title": "Examples", "content": "Examples work correctly"},
                        ],
                    },
                ],
            }
        ],
    }
    linter = PlanLinter({})

    # when
    errors = linter.lint(yaml_data)

    # then
    assert len(errors) == 0  # type: ignore[arg-type]


async def test_plan_linter__if_circular_dependency__detects_error() -> None:
    # given
    plan_a = create_test_plan("plan-a", [], depends_on=["plan-b"])
    plan_b_doc = create_test_plan("plan-b", [], depends_on=["plan-a"])
    plan_a.work_plans.append(plan_b_doc.work_plans[0])
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    # when
    errors = linter.validate_depends_on(plan_a, plan_path)

    # then
    assert len(errors) > 0
    assert any("circular" in error.lower() for error in errors)


async def test_plan_linter__if_missing_dependency__detects_error() -> None:
    # given
    plan_doc = create_test_plan("test-plan", [], depends_on=["nonexistent-plan"])
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    # when
    errors = linter.validate_depends_on(plan_doc, plan_path)

    # then
    assert len(errors) > 0
