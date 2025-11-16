"""
Tests for acceptance_criteria_for_verification_agent reset logic.

Tests that when ExecutionStatus.fully_done_at is set to None,
acceptance_criteria_for_verification_agent's checked_at and checked_evidence
fields are reset to None via the WorkPlan model_validator.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaChecklist,
    AcceptanceCriteriaForVerificationAgent,
    WorkPlan,
)
from sisyphus_core.core.plans.template import PlanTemplateGenerator

pytestmark = [pytest.mark.anyio]


async def test_workplan__if_fully_done_at_none__resets_all_checklists() -> None:
    """Given: WorkPlan with acceptance criteria with checked_at/checked_evidence set.
    When: WorkPlan is constructed with execution.fully_done_at = None.
    Then: All checked_at and checked_evidence fields should be reset to None.
    """
    # Given
    template_gen = PlanTemplateGenerator()
    plan_doc = template_gen.full_example()
    work_plan = plan_doc.work_plans[0]

    checklist_1 = AcceptanceCriteriaChecklist(
        id="check-1",
        title="First check",
        content="Check something",
        checked_at="2025-11-16T10:00:00Z",
        checked_evidence="Evidence 1",
    )
    checklist_2 = AcceptanceCriteriaChecklist(
        id="check-2",
        title="Second check",
        content="Check another thing",
        checked_at="2025-11-16T10:05:00Z",
        checked_evidence="Evidence 2",
    )

    criteria = AcceptanceCriteriaForVerificationAgent(
        id="criteria-1",
        title="Test Criteria",
        accepted_at="2025-11-16T10:10:00Z",
        checklists=[checklist_1, checklist_2],
    )

    work_plan.acceptance_criteria_for_verification_agent = [criteria]

    # When: Create a new WorkPlan instance with fully_done_at = None to trigger validator
    new_plan = WorkPlan(
        id=work_plan.id,
        name=work_plan.name,
        depends_on=work_plan.depends_on,
        user_request=work_plan.user_request,
        objectives=work_plan.objectives,
        background=work_plan.background,
        required_background=work_plan.required_background,
        workflow=work_plan.workflow,
        success_vision=work_plan.success_vision,
        final_verification=work_plan.final_verification,
        todos=work_plan.todos,
        references=work_plan.references,
        execution=work_plan.execution,
        work_mode=work_plan.work_mode,
        current_work=work_plan.current_work,
        current_work_ids=work_plan.current_work_ids,
        acceptance_criteria_for_verification_agent=work_plan.acceptance_criteria_for_verification_agent,
        fully_done_evidence=work_plan.fully_done_evidence,
    )

    # Then: Verify that acceptance criteria checklists are reset
    for criteria_item in new_plan.acceptance_criteria_for_verification_agent:
        for checklist in criteria_item.checklists:
            assert (
                checklist.checked_at is None
            ), f"Expected checked_at to be None but got {checklist.checked_at}"
            assert checklist.checked_evidence is None


async def test_workplan__if_fully_done_at_set__preserves_checklists() -> None:
    """Given: WorkPlan with acceptance criteria with checked_at/checked_evidence set.
    When: WorkPlan is constructed with execution.fully_done_at = some timestamp.
    Then: All checked_at and checked_evidence fields should be preserved.
    """
    # Given
    template_gen = PlanTemplateGenerator()
    plan_doc = template_gen.full_example()
    work_plan = plan_doc.work_plans[0]

    checklist = AcceptanceCriteriaChecklist(
        id="check-1",
        title="First check",
        content="Check something",
        checked_at="2025-11-16T10:00:00Z",
        checked_evidence="Evidence 1",
    )

    criteria = AcceptanceCriteriaForVerificationAgent(
        id="criteria-1",
        title="Test Criteria",
        accepted_at="2025-11-16T10:10:00Z",
        checklists=[checklist],
    )

    work_plan.acceptance_criteria_for_verification_agent = [criteria]
    work_plan.execution.fully_done_at = "2025-11-16T11:00:00Z"

    # When: Create new instance to trigger validator with fully_done_at set
    new_plan = WorkPlan(
        id=work_plan.id,
        name=work_plan.name,
        depends_on=work_plan.depends_on,
        user_request=work_plan.user_request,
        objectives=work_plan.objectives,
        background=work_plan.background,
        required_background=work_plan.required_background,
        workflow=work_plan.workflow,
        success_vision=work_plan.success_vision,
        final_verification=work_plan.final_verification,
        todos=work_plan.todos,
        references=work_plan.references,
        execution=work_plan.execution,
        work_mode=work_plan.work_mode,
        current_work=work_plan.current_work,
        current_work_ids=work_plan.current_work_ids,
        acceptance_criteria_for_verification_agent=work_plan.acceptance_criteria_for_verification_agent,
        fully_done_evidence=work_plan.fully_done_evidence,
    )

    # Then: Verify that acceptance criteria checklists are NOT reset
    for criteria_item in new_plan.acceptance_criteria_for_verification_agent:
        for checklist in criteria_item.checklists:
            assert checklist.checked_at == "2025-11-16T10:00:00Z"
            assert checklist.checked_evidence == "Evidence 1"


async def test_workplan__if_multiple_criteria__resets_all() -> None:
    """Given: WorkPlan with multiple acceptance criteria, each with multiple checklists.
    When: WorkPlan is constructed with execution.fully_done_at = None.
    Then: All checked_at and checked_evidence fields across all criteria should be reset.
    """
    # Given
    template_gen = PlanTemplateGenerator()
    plan_doc = template_gen.full_example()
    work_plan = plan_doc.work_plans[0]

    criteria_list: list[AcceptanceCriteriaForVerificationAgent] = []
    for i in range(3):
        checklists: list[AcceptanceCriteriaChecklist] = []
        for j in range(2):
            checklist = AcceptanceCriteriaChecklist(
                id=f"check-{i}-{j}",
                title=f"Checklist {i}-{j}",
                content=f"Content {i}-{j}",
                checked_at=f"2025-11-16T10:{i:02d}:{j:02d}Z",
                checked_evidence=f"Evidence {i}-{j}",
            )
            checklists.append(checklist)

        criteria = AcceptanceCriteriaForVerificationAgent(
            id=f"criteria-{i}",
            title=f"Criteria {i}",
            accepted_at=f"2025-11-16T10:10:{i:02d}Z",
            checklists=checklists,
        )
        criteria_list.append(criteria)

    work_plan.acceptance_criteria_for_verification_agent = criteria_list
    work_plan.execution.fully_done_at = None

    # When: Create new instance to trigger validator
    new_plan = WorkPlan(
        id=work_plan.id,
        name=work_plan.name,
        depends_on=work_plan.depends_on,
        user_request=work_plan.user_request,
        objectives=work_plan.objectives,
        background=work_plan.background,
        required_background=work_plan.required_background,
        workflow=work_plan.workflow,
        success_vision=work_plan.success_vision,
        final_verification=work_plan.final_verification,
        todos=work_plan.todos,
        references=work_plan.references,
        execution=work_plan.execution,
        work_mode=work_plan.work_mode,
        current_work=work_plan.current_work,
        current_work_ids=work_plan.current_work_ids,
        acceptance_criteria_for_verification_agent=work_plan.acceptance_criteria_for_verification_agent,
        fully_done_evidence=work_plan.fully_done_evidence,
    )

    # Then: Verify ALL checklists in ALL criteria are reset
    for criteria_item in new_plan.acceptance_criteria_for_verification_agent:
        for checklist in criteria_item.checklists:
            assert checklist.checked_at is None
            assert checklist.checked_evidence is None


async def test_workplan__if_reset_and_reloaded__persists() -> None:
    """Given: WorkPlan with checked acceptance criteria saved to disk.
    When: WorkPlan is reloaded, fully_done_at set to None, and saved again.
    Then: The reset criteria should persist after reload.
    """
    # Given
    with TemporaryDirectory() as temp_dir:
        plan_path = Path(temp_dir) / "test_plan.yaml"

        template_gen = PlanTemplateGenerator()
        plan_doc = template_gen.full_example()
        work_plan = plan_doc.work_plans[0]

        checklist = AcceptanceCriteriaChecklist(
            id="check-1",
            title="First check",
            content="Check something",
            checked_at="2025-11-16T10:00:00Z",
            checked_evidence="Evidence 1",
        )

        criteria = AcceptanceCriteriaForVerificationAgent(
            id="criteria-1",
            title="Test Criteria",
            checklists=[checklist],
        )

        work_plan.acceptance_criteria_for_verification_agent = [criteria]
        work_plan.execution.fully_done_at = "2025-11-16T11:00:00Z"

        await save_plan(plan_path, plan_doc)

        # When: Load, reset fully_done_at, and save
        loaded_plan = await load_plan(plan_path)
        work_plan_reset = loaded_plan.work_plans[0]
        work_plan_reset.execution.fully_done_at = None

        new_plan = WorkPlan(
            id=work_plan_reset.id,
            name=work_plan_reset.name,
            depends_on=work_plan_reset.depends_on,
            user_request=work_plan_reset.user_request,
            objectives=work_plan_reset.objectives,
            background=work_plan_reset.background,
            required_background=work_plan_reset.required_background,
            workflow=work_plan_reset.workflow,
            success_vision=work_plan_reset.success_vision,
            final_verification=work_plan_reset.final_verification,
            todos=work_plan_reset.todos,
            references=work_plan_reset.references,
            execution=work_plan_reset.execution,
            work_mode=work_plan_reset.work_mode,
            current_work=work_plan_reset.current_work,
            current_work_ids=work_plan_reset.current_work_ids,
            acceptance_criteria_for_verification_agent=work_plan_reset.acceptance_criteria_for_verification_agent,
            fully_done_evidence=work_plan_reset.fully_done_evidence,
        )

        loaded_plan.work_plans[0] = new_plan
        await save_plan(plan_path, loaded_plan)

        # Then: Reload and verify acceptance criteria are still reset
        reloaded_plan = await load_plan(plan_path)
        for criteria_item in reloaded_plan.work_plans[0].acceptance_criteria_for_verification_agent:
            for checklist in criteria_item.checklists:
                assert checklist.checked_at is None
                assert checklist.checked_evidence is None


async def test_workplan__if_empty_criteria__handles_gracefully() -> None:
    """Given: WorkPlan with empty acceptance_criteria_for_verification_agent list.
    When: WorkPlan is constructed with execution.fully_done_at = None.
    Then: No errors should occur and plan should be created successfully.
    """
    # Given
    template_gen = PlanTemplateGenerator()
    plan_doc = template_gen.full_example()
    work_plan = plan_doc.work_plans[0]

    work_plan.acceptance_criteria_for_verification_agent = []
    work_plan.execution.fully_done_at = None

    # When: Create new instance with empty criteria
    new_plan = WorkPlan(
        id=work_plan.id,
        name=work_plan.name,
        depends_on=work_plan.depends_on,
        user_request=work_plan.user_request,
        objectives=work_plan.objectives,
        background=work_plan.background,
        required_background=work_plan.required_background,
        workflow=work_plan.workflow,
        success_vision=work_plan.success_vision,
        final_verification=work_plan.final_verification,
        todos=work_plan.todos,
        references=work_plan.references,
        execution=work_plan.execution,
        work_mode=work_plan.work_mode,
        current_work=work_plan.current_work,
        current_work_ids=work_plan.current_work_ids,
        acceptance_criteria_for_verification_agent=work_plan.acceptance_criteria_for_verification_agent,
        fully_done_evidence=work_plan.fully_done_evidence,
    )

    # Then: No error should occur, and criteria should remain empty
    assert new_plan.acceptance_criteria_for_verification_agent == []
