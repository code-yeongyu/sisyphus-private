from pathlib import Path

import pytest

from sisyphus_core.core.plans.loader import load_plan
from sisyphus_core.core.plans.models import PlanDocument

pytestmark = [pytest.mark.anyio]


async def test_load_plan__with_new_userrequest_fields__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    assert len(plan_doc.work_plans) > 0
    work_plan = plan_doc.work_plans[0]
    assert work_plan.user_request.expected_outcome is not None
    assert work_plan.user_request.forbidden_outcome is not None
    assert work_plan.user_request.expected_outcome == "All new fields should be properly parsed and accessible"
    assert work_plan.user_request.forbidden_outcome == "The plan should not fail to load due to missing fields"


async def test_load_plan__with_todo_parallel_field__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]
    assert len(work_plan.todos) > 0

    # Check first todo (should have parallel=False)
    todo1 = work_plan.todos[0]
    assert hasattr(todo1, "parallel")
    assert todo1.parallel is False

    # Check second todo (should have parallel=True)
    todo2 = work_plan.todos[1]
    assert hasattr(todo2, "parallel")
    assert todo2.parallel is True
    assert todo2.parallelable_and_safe_evidence == "This task can run in parallel with others"


async def test_load_plan__with_todo_acceptance_criteria__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]
    todo = work_plan.todos[0]

    assert hasattr(todo, "acceptance_criteria")
    assert len(todo.acceptance_criteria) > 0

    criterion = todo.acceptance_criteria[0]
    assert criterion.id == "criterion-1"
    assert criterion.condition == "UserRequest has expected_outcome field"
    assert criterion.verified_at is None
    assert criterion.verification_evidence is None


async def test_load_plan__with_deterministic_bash_verification__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]
    todo = work_plan.todos[0]

    assert len(todo.verification_spec) > 0
    verif = todo.verification_spec[0]

    assert hasattr(verif, "deterministic_bash")
    assert len(verif.deterministic_bash) > 0

    deterministic = verif.deterministic_bash[0]
    assert deterministic.description == "Verify expected_outcome field exists"
    assert deterministic.reason_why_it_is_deterministic_and_reliable == "Pydantic model validation is deterministic"
    assert deterministic.execute == "echo 'expected_outcome check'"
    assert deterministic.expected_stdout == "expected_outcome check"
    assert deterministic.expected_exit_code == 0
    assert deterministic.verified_at is None


async def test_load_plan__with_orchestrator_judge_verification__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]
    todo = work_plan.todos[1]

    assert len(todo.verification_spec) > 0
    verif = todo.verification_spec[0]

    assert hasattr(verif, "orchestrator_judge")
    assert len(verif.orchestrator_judge) > 0

    judge = verif.orchestrator_judge[0]
    assert judge.prompt == "Are all Todo fields properly typed?"
    assert judge.verified_at is None
    assert judge.verification_evidence is None


async def test_load_plan__with_workplan_current_work_ids__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]

    assert hasattr(work_plan, "current_work_ids")
    assert isinstance(work_plan.current_work_ids, list)
    assert len(work_plan.current_work_ids) > 0
    assert "test-1" in work_plan.current_work_ids
    assert "test-2" in work_plan.current_work_ids


async def test_load_plan__with_acceptance_criteria_for_verification_agent__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]

    assert hasattr(work_plan, "acceptance_criteria_for_verification_agent")
    assert len(work_plan.acceptance_criteria_for_verification_agent) > 0

    criteria = work_plan.acceptance_criteria_for_verification_agent[0]
    assert criteria.id == "acceptance-1"
    assert criteria.title == "All UserRequest fields parsed"
    assert criteria.accepted_at is None
    assert len(criteria.checklists) > 0

    checklist = criteria.checklists[0]
    assert checklist.id == "checklist-1"
    assert checklist.title == "expected_outcome accessible"
    assert checklist.content == "UserRequest.expected_outcome should be accessible"
    assert checklist.checked_at is None
    assert checklist.checked_evidence is None


async def test_load_plan__with_execution_status_fully_done_at__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]

    assert hasattr(work_plan.execution, "fully_done_at")
    assert work_plan.execution.fully_done_at is None
    assert work_plan.execution.started is False
    assert work_plan.execution.completed is False


async def test_load_plan__with_workplan_fully_done_evidence__parses_correctly() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]

    assert hasattr(work_plan, "fully_done_evidence")
    assert work_plan.fully_done_evidence is None


async def test_load_plan__verifies_all_new_fields_accessible__comprehensive() -> None:
    # Given
    plan_path = Path("/Users/yeongyu/local-workspaces/sisyphus/example-new-plan.yaml")

    # When
    plan_doc: PlanDocument = await load_plan(plan_path)

    # Then
    assert plan_doc is not None
    work_plan = plan_doc.work_plans[0]

    # UserRequest new fields
    assert hasattr(work_plan.user_request, "expected_outcome")
    assert hasattr(work_plan.user_request, "forbidden_outcome")

    # Todo new fields
    todo = work_plan.todos[0]
    assert hasattr(todo, "parallel")
    assert hasattr(todo, "parallelable_and_safe_evidence")
    assert hasattr(todo, "acceptance_criteria")

    # VerificationItem new fields
    verif = todo.verification_spec[0]
    assert hasattr(verif, "deterministic_bash")
    assert hasattr(verif, "orchestrator_judge")

    # WorkPlan new fields
    assert hasattr(work_plan, "current_work_ids")
    assert hasattr(work_plan, "acceptance_criteria_for_verification_agent")
    assert hasattr(work_plan, "fully_done_evidence")

    # ExecutionStatus new fields
    assert hasattr(work_plan.execution, "fully_done_at")
