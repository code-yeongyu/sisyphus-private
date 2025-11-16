"""Test automatic reset of acceptance criteria when fully_done_at is set to None."""

from __future__ import annotations

import pytest

from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaChecklist,
    AcceptanceCriteriaForVerificationAgent,
    ExecutionStatus,
    WorkMode,
    WorkPlan,
)


@pytest.mark.anyio()
async def test_acceptance_reset__if_fully_done_at_none__then_criteria_reset() -> None:
    """Given: WorkPlan with acceptance criteria all checked.
    When: execution.fully_done_at is set to None.
    Then: All checked_at and checked_evidence should be automatically reset.
    """
    # Given
    checklist = AcceptanceCriteriaChecklist(
        id="test-criterion-1",
        title="Test Criterion",
        content="This is a test criterion",
        checked_at="2025-11-16T10:00:00Z",
        checked_evidence="Verified by test",
    )
    criteria = AcceptanceCriteriaForVerificationAgent(
        id="criteria-1",
        title="Test Criteria Group",
        accepted_at="2025-11-16T10:00:00Z",
        checklists=[checklist],
    )
    work_plan = WorkPlan(
        id="test-plan",
        name="Test Plan",
        user_request={"original": "test", "created_at": "2025-11-16T10:00:00Z", "additional": []},
        objectives={"core": "test", "detailed": []},
        background={"current_situation": "test", "reason_for_change": "test", "changes_to_make": "test"},
        required_background={"description": "test", "file_structure": "test", "references": []},
        workflow={"dependency_diagram": "test", "critical_path": []},
        success_vision={"user_perspective": [], "business_perspective": [], "technical_criteria": []},
        final_verification=[],
        todos=[],
        execution=ExecutionStatus(
            started=False, completed=False, started_at=None, completed_at=None, fully_done_at="2025-11-16T10:00:00Z"
        ),
        work_mode=WorkMode(parallel_requested=False),
        acceptance_criteria_for_verification_agent=[criteria],
    )

    # Verify initial state
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at is not None
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence is not None

    # When - Create new instance with fully_done_at = None
    work_plan_reset = WorkPlan(
        id="test-plan",
        name="Test Plan",
        user_request={"original": "test", "created_at": "2025-11-16T10:00:00Z", "additional": []},
        objectives={"core": "test", "detailed": []},
        background={"current_situation": "test", "reason_for_change": "test", "changes_to_make": "test"},
        required_background={"description": "test", "file_structure": "test", "references": []},
        workflow={"dependency_diagram": "test", "critical_path": []},
        success_vision={"user_perspective": [], "business_perspective": [], "technical_criteria": []},
        final_verification=[],
        todos=[],
        execution=ExecutionStatus(
            started=False, completed=False, started_at=None, completed_at=None, fully_done_at=None
        ),
        work_mode=WorkMode(parallel_requested=False),
        acceptance_criteria_for_verification_agent=[
            AcceptanceCriteriaForVerificationAgent(
                id="criteria-1",
                title="Test Criteria Group",
                accepted_at="2025-11-16T10:00:00Z",
                checklists=[
                    AcceptanceCriteriaChecklist(
                        id="test-criterion-1",
                        title="Test Criterion",
                        content="This is a test criterion",
                        checked_at="2025-11-16T10:00:00Z",
                        checked_evidence="Verified by test",
                    )
                ],
            )
        ],
    )

    # Then - Model validator should have reset the criteria
    assert work_plan_reset.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at is None
    assert work_plan_reset.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence is None


@pytest.mark.anyio()
async def test_acceptance_reset__if_fully_done_at_not_none__then_criteria_unchanged() -> None:
    """Given: WorkPlan with fully_done_at set to a timestamp.
    When: Instance is created with fully_done_at not None.
    Then: acceptance_criteria should NOT be reset.
    """
    # Given + When
    work_plan = WorkPlan(
        id="test-plan",
        name="Test Plan",
        user_request={"original": "test", "created_at": "2025-11-16T10:00:00Z", "additional": []},
        objectives={"core": "test", "detailed": []},
        background={"current_situation": "test", "reason_for_change": "test", "changes_to_make": "test"},
        required_background={"description": "test", "file_structure": "test", "references": []},
        workflow={"dependency_diagram": "test", "critical_path": []},
        success_vision={"user_perspective": [], "business_perspective": [], "technical_criteria": []},
        final_verification=[],
        todos=[],
        execution=ExecutionStatus(
            started=False, completed=False, started_at=None, completed_at=None, fully_done_at="2025-11-16T11:00:00Z"
        ),
        work_mode=WorkMode(parallel_requested=False),
        acceptance_criteria_for_verification_agent=[
            AcceptanceCriteriaForVerificationAgent(
                id="criteria-1",
                title="Test Criteria Group",
                accepted_at="2025-11-16T10:00:00Z",
                checklists=[
                    AcceptanceCriteriaChecklist(
                        id="test-criterion-1",
                        title="Test Criterion",
                        content="This is a test criterion",
                        checked_at="2025-11-16T10:00:00Z",
                        checked_evidence="Verified by test",
                    )
                ],
            )
        ],
    )

    # Then - criteria should remain unchanged
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at == "2025-11-16T10:00:00Z"
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence == "Verified by test"


@pytest.mark.anyio()
async def test_acceptance_reset__if_multiple_checklists__then_all_reset() -> None:
    """Given: WorkPlan with multiple checklists all checked.
    When: fully_done_at is None.
    Then: All checklists should be reset.
    """
    # Given + When
    work_plan = WorkPlan(
        id="test-plan",
        name="Test Plan",
        user_request={"original": "test", "created_at": "2025-11-16T10:00:00Z", "additional": []},
        objectives={"core": "test", "detailed": []},
        background={"current_situation": "test", "reason_for_change": "test", "changes_to_make": "test"},
        required_background={"description": "test", "file_structure": "test", "references": []},
        workflow={"dependency_diagram": "test", "critical_path": []},
        success_vision={"user_perspective": [], "business_perspective": [], "technical_criteria": []},
        final_verification=[],
        todos=[],
        execution=ExecutionStatus(
            started=False, completed=False, started_at=None, completed_at=None, fully_done_at=None
        ),
        work_mode=WorkMode(parallel_requested=False),
        acceptance_criteria_for_verification_agent=[
            AcceptanceCriteriaForVerificationAgent(
                id="criteria-1",
                title="Criteria Group 1",
                accepted_at="2025-11-16T10:00:00Z",
                checklists=[
                    AcceptanceCriteriaChecklist(
                        id="criterion-1-1",
                        title="Criterion 1.1",
                        content="Content 1.1",
                        checked_at="2025-11-16T10:00:00Z",
                        checked_evidence="Evidence 1.1",
                    ),
                    AcceptanceCriteriaChecklist(
                        id="criterion-1-2",
                        title="Criterion 1.2",
                        content="Content 1.2",
                        checked_at="2025-11-16T10:00:00Z",
                        checked_evidence="Evidence 1.2",
                    ),
                ],
            ),
            AcceptanceCriteriaForVerificationAgent(
                id="criteria-2",
                title="Criteria Group 2",
                accepted_at="2025-11-16T10:00:00Z",
                checklists=[
                    AcceptanceCriteriaChecklist(
                        id="criterion-2-1",
                        title="Criterion 2.1",
                        content="Content 2.1",
                        checked_at="2025-11-16T10:00:00Z",
                        checked_evidence="Evidence 2.1",
                    ),
                ],
            ),
        ],
    )

    # Then - all checklists should be reset
    for criteria in work_plan.acceptance_criteria_for_verification_agent:
        for checklist in criteria.checklists:
            assert checklist.checked_at is None, f"Expected {checklist.id} checked_at to be None"
            assert checklist.checked_evidence is None, f"Expected {checklist.id} checked_evidence to be None"


@pytest.mark.anyio()
async def test_acceptance_reset__if_yaml_roundtrip_with_fully_done_none__then_criteria_reset() -> None:
    """Given: WorkPlan with checked acceptance criteria is serialized to dict.
    When: YAML file is edited to set fully_done_at to None and reloaded (simulated by dict -> model).
    Then: All checked_at and checked_evidence should be automatically reset.

    This simulates the ACTUAL use case: YAML file is saved, edited to set fully_done_at=None,
    and reloaded. The model_validator triggers on reload because a NEW model instance is created.
    """
    # Given - initial state with checked criteria
    initial_data = {
        "id": "test-plan",
        "name": "Test Plan",
        "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z", "additional": []},
        "objectives": {"core": "test", "detailed": []},
        "background": {"current_situation": "test", "reason_for_change": "test", "changes_to_make": "test"},
        "required_background": {"description": "test", "file_structure": "test", "references": []},
        "workflow": {"dependency_diagram": "test", "critical_path": []},
        "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
        "final_verification": [],
        "todos": [],
        "execution": {
            "started": False,
            "completed": False,
            "started_at": None,
            "completed_at": None,
            "fully_done_at": "2025-11-16T10:00:00Z",
        },
        "work_mode": {"parallel_requested": False},
        "acceptance_criteria_for_verification_agent": [
            {
                "id": "criteria-1",
                "title": "Test Criteria",
                "accepted_at": "2025-11-16T10:00:00Z",
                "checklists": [
                    {
                        "id": "criterion-1",
                        "title": "Test",
                        "content": "Content",
                        "checked_at": "2025-11-16T10:00:00Z",
                        "checked_evidence": "Evidence",
                    }
                ],
            }
        ],
    }

    # Create initial WorkPlan
    work_plan_initial = WorkPlan.model_validate(initial_data)

    # Verify initial state - criteria should NOT be reset (fully_done_at is set)
    assert work_plan_initial.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at is not None
    assert work_plan_initial.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence is not None

    # When - Simulate YAML file edit: change fully_done_at to None
    # This is what happens when someone edits the YAML file and sets fully_done_at: null
    modified_data = initial_data.copy()
    modified_data["execution"] = {
        "started": False,
        "completed": False,
        "started_at": None,
        "completed_at": None,
        "fully_done_at": None,  # <-- YAML edited to null
    }

    # Reload from modified "YAML" (simulated by dict)
    work_plan_reloaded = WorkPlan.model_validate(modified_data)

    # Then - model_validator should have reset the criteria on reload
    assert work_plan_reloaded.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at is None
    assert work_plan_reloaded.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence is None


@pytest.mark.anyio()
async def test_acceptance_reset__if_model_validate_called__then_validator_runs() -> None:
    """Given: WorkPlan dict data with fully_done_at = None.
    When: model_validate() is called (like during YAML deserialization).
    Then: model_validator runs and resets acceptance criteria.

    This tests the Pydantic 2.x behavior: model_validate() triggers validators.
    """
    # Given
    data = {
        "id": "test-plan",
        "name": "Test Plan",
        "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z", "additional": []},
        "objectives": {"core": "test", "detailed": []},
        "background": {"current_situation": "test", "reason_for_change": "test", "changes_to_make": "test"},
        "required_background": {"description": "test", "file_structure": "test", "references": []},
        "workflow": {"dependency_diagram": "test", "critical_path": []},
        "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
        "final_verification": [],
        "todos": [],
        "execution": {
            "started": False,
            "completed": False,
            "started_at": None,
            "completed_at": None,
            "fully_done_at": None,
        },
        "work_mode": {"parallel_requested": False},
        "acceptance_criteria_for_verification_agent": [
            {
                "id": "criteria-1",
                "title": "Test Criteria",
                "accepted_at": "2025-11-16T10:00:00Z",
                "checklists": [
                    {
                        "id": "criterion-1",
                        "title": "Test",
                        "content": "Content",
                        "checked_at": "2025-11-16T10:00:00Z",
                        "checked_evidence": "Evidence",
                    }
                ],
            }
        ],
    }

    # When - call model_validate (like YAML loader does)
    work_plan = WorkPlan.model_validate(data)

    # Then - model_validator should have reset the criteria
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at is None
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence is None


@pytest.mark.anyio()
async def test_acceptance_reset__if_set_fully_done_at_called_with_none__then_criteria_reset() -> None:
    """Given: WorkPlan with acceptance criteria all checked and fully_done_at set.
    When: set_fully_done_at(None) is called.
    Then: All checked_at and checked_evidence should be automatically reset.

    This tests the explicit method for resetting acceptance criteria when changing fully_done_at.
    """
    # Given
    work_plan = WorkPlan.model_validate(
        {
            "id": "test-plan",
            "name": "Test Plan",
            "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z", "additional": []},
            "objectives": {"core": "test", "detailed": []},
            "background": {"current_situation": "test", "reason_for_change": "test", "changes_to_make": "test"},
            "required_background": {"description": "test", "file_structure": "test", "references": []},
            "workflow": {"dependency_diagram": "test", "critical_path": []},
            "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
            "final_verification": [],
            "todos": [],
            "execution": {
                "started": False,
                "completed": False,
                "started_at": None,
                "completed_at": None,
                "fully_done_at": "2025-11-16T10:00:00Z",
            },
            "work_mode": {"parallel_requested": False},
            "acceptance_criteria_for_verification_agent": [
                {
                    "id": "criteria-1",
                    "title": "Test Criteria Group",
                    "accepted_at": "2025-11-16T10:00:00Z",
                    "checklists": [
                        {
                            "id": "test-criterion-1",
                            "title": "Test Criterion",
                            "content": "This is a test criterion",
                            "checked_at": "2025-11-16T10:00:00Z",
                            "checked_evidence": "Verified by test",
                        }
                    ],
                }
            ],
        }
    )

    # Given - criteria should NOT be reset (fully_done_at is set)
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at is not None
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence is not None
    assert work_plan.execution.fully_done_at == "2025-11-16T10:00:00Z"

    # When
    work_plan.set_fully_done_at(None)

    # Then
    assert work_plan.execution.fully_done_at is None
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at is None
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence is None


@pytest.mark.anyio()
async def test_acceptance_reset__if_set_fully_done_at_called_with_value__then_criteria_unchanged() -> None:
    """Given: WorkPlan with acceptance criteria all checked.
    When: set_fully_done_at() is called with a non-None value.
    Then: acceptance_criteria should NOT be reset.
    """
    # Given
    work_plan = WorkPlan.model_validate(
        {
            "id": "test-plan",
            "name": "Test Plan",
            "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z", "additional": []},
            "objectives": {"core": "test", "detailed": []},
            "background": {"current_situation": "test", "reason_for_change": "test", "changes_to_make": "test"},
            "required_background": {"description": "test", "file_structure": "test", "references": []},
            "workflow": {"dependency_diagram": "test", "critical_path": []},
            "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
            "final_verification": [],
            "todos": [],
            "execution": {
                "started": False,
                "completed": False,
                "started_at": None,
                "completed_at": None,
                "fully_done_at": "2025-11-16T10:00:00Z",
            },
            "work_mode": {"parallel_requested": False},
            "acceptance_criteria_for_verification_agent": [
                {
                    "id": "criteria-1",
                    "title": "Test Criteria Group",
                    "accepted_at": "2025-11-16T10:00:00Z",
                    "checklists": [
                        {
                            "id": "test-criterion-1",
                            "title": "Test Criterion",
                            "content": "This is a test criterion",
                            "checked_at": "2025-11-16T10:00:00Z",
                            "checked_evidence": "Verified by test",
                        }
                    ],
                }
            ],
        }
    )

    # Given
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at == "2025-11-16T10:00:00Z"

    # When
    work_plan.set_fully_done_at("2025-11-16T12:00:00Z")

    # Then
    assert work_plan.execution.fully_done_at == "2025-11-16T12:00:00Z"
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_at == "2025-11-16T10:00:00Z"
    assert work_plan.acceptance_criteria_for_verification_agent[0].checklists[0].checked_evidence == "Verified by test"
