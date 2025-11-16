"""
Tests for acceptance_criteria_for_verification_agent reset logic.

Tests that WorkPlan.reset_acceptance_criteria() explicitly resets
checked_at and checked_evidence fields when called.

NOTE: The reset is now EXPLICIT (not automatic on construction) to prevent
data loss during YAML deserialization.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaChecklist,
    AcceptanceCriteriaForVerificationAgent,
)
from sisyphus_core.core.plans.template import PlanTemplateGenerator

pytestmark = [pytest.mark.anyio]


async def test_workplan__reset_acceptance_criteria__resets_all_checklists() -> None:
    """Given: WorkPlan with acceptance criteria with checked_at/checked_evidence set.
    When: reset_acceptance_criteria() is called.
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

    # When: Explicitly call reset method
    work_plan.reset_acceptance_criteria()

    # Then: Verify that acceptance criteria checklists are reset
    for criteria_item in work_plan.acceptance_criteria_for_verification_agent:
        for checklist in criteria_item.checklists:
            assert checklist.checked_at is None, f"Expected checked_at to be None but got {checklist.checked_at}"
            assert checklist.checked_evidence is None


async def test_workplan__without_reset__preserves_checklists() -> None:
    """Given: WorkPlan with acceptance criteria with checked_at/checked_evidence set.
    When: WorkPlan is loaded without calling reset_acceptance_criteria().
    Then: All checked_at and checked_evidence fields should be preserved.
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
            accepted_at="2025-11-16T10:10:00Z",
            checklists=[checklist],
        )

        work_plan.acceptance_criteria_for_verification_agent = [criteria]
        await save_plan(plan_path, plan_doc)

        # When: Load without calling reset
        loaded_plan = await load_plan(plan_path)

        # Then: Verify that acceptance criteria checklists are NOT reset (NO DATA LOSS)
        for criteria_item in loaded_plan.work_plans[0].acceptance_criteria_for_verification_agent:
            for checklist_item in criteria_item.checklists:
                assert checklist_item.checked_at == "2025-11-16T10:00:00Z"
                assert checklist_item.checked_evidence == "Evidence 1"


async def test_workplan__reset_multiple_criteria__resets_all() -> None:
    """Given: WorkPlan with multiple acceptance criteria, each with multiple checklists.
    When: reset_acceptance_criteria() is called.
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

    # When: Call reset method
    work_plan.reset_acceptance_criteria()

    # Then: Verify ALL checklists in ALL criteria are reset
    for criteria_item in work_plan.acceptance_criteria_for_verification_agent:
        for checklist in criteria_item.checklists:
            assert checklist.checked_at is None
            assert checklist.checked_evidence is None


async def test_workplan__reset_then_save_reload__persists() -> None:
    """Given: WorkPlan with checked acceptance criteria.
    When: reset_acceptance_criteria() is called, saved, and reloaded.
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

        await save_plan(plan_path, plan_doc)

        # When: Load, reset, and save
        loaded_plan = await load_plan(plan_path)
        loaded_plan.work_plans[0].reset_acceptance_criteria()
        await save_plan(plan_path, loaded_plan)

        # Then: Reload and verify acceptance criteria are still reset
        reloaded_plan = await load_plan(plan_path)
        for criteria_item in reloaded_plan.work_plans[0].acceptance_criteria_for_verification_agent:
            for checklist_item in criteria_item.checklists:
                assert checklist_item.checked_at is None
                assert checklist_item.checked_evidence is None


async def test_workplan__reset_empty_criteria__handles_gracefully() -> None:
    """Given: WorkPlan with empty acceptance_criteria_for_verification_agent list.
    When: reset_acceptance_criteria() is called.
    Then: No errors should occur.
    """
    # Given
    template_gen = PlanTemplateGenerator()
    plan_doc = template_gen.full_example()
    work_plan = plan_doc.work_plans[0]

    work_plan.acceptance_criteria_for_verification_agent = []

    # When: Call reset on empty criteria
    work_plan.reset_acceptance_criteria()

    # Then: No error should occur, and criteria should remain empty
    assert work_plan.acceptance_criteria_for_verification_agent == []


async def test_workplan__no_data_loss_on_reload() -> None:
    """Given: WorkPlan with checked_at and checked_evidence set.
    When: Save and reload the plan multiple times.
    Then: No data loss should occur (critical regression test).
    """
    # Given
    with TemporaryDirectory() as temp_dir:
        plan_path = Path(temp_dir) / "test_plan.yaml"

        template_gen = PlanTemplateGenerator()
        plan_doc = template_gen.full_example()
        work_plan = plan_doc.work_plans[0]

        original_checked_at = "2025-11-16T10:00:00Z"
        original_evidence = "Critical evidence that MUST be preserved"

        checklist = AcceptanceCriteriaChecklist(
            id="check-1",
            title="Critical check",
            content="Important verification",
            checked_at=original_checked_at,
            checked_evidence=original_evidence,
        )

        criteria = AcceptanceCriteriaForVerificationAgent(
            id="criteria-1",
            title="Critical Criteria",
            checklists=[checklist],
        )

        work_plan.acceptance_criteria_for_verification_agent = [criteria]
        work_plan.execution.completed = True
        work_plan.execution.fully_done_at = None  # This used to cause DATA LOSS

        await save_plan(plan_path, plan_doc)

        # When: Reload multiple times
        for _ in range(3):
            reloaded = await load_plan(plan_path)
            await save_plan(plan_path, reloaded)

        final_plan = await load_plan(plan_path)

        # Then: NO DATA LOSS - values MUST be preserved
        actual_checklist = final_plan.work_plans[0].acceptance_criteria_for_verification_agent[0].checklists[0]
        assert actual_checklist.checked_at == original_checked_at, (
            f"DATA LOSS: checked_at changed from {original_checked_at} to {actual_checklist.checked_at}"
        )
        assert actual_checklist.checked_evidence == original_evidence, (
            f"DATA LOSS: evidence changed from {original_evidence} to {actual_checklist.checked_evidence}"
        )
