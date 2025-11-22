from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaItem,
    DeterministicBashVerification,
    ExecutionStatus,
    PlanDocument,
    UserRequest,
)
from sisyphus_core.core.plans.template import PlanTemplateGenerator


def test_full_example__includes_user_request_expected_outcome__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    assert len(plan_doc.work_plans) > 0
    work_plan = plan_doc.work_plans[0]
    assert isinstance(work_plan.user_request, UserRequest)
    assert hasattr(work_plan.user_request, "expected_outcome")
    assert work_plan.user_request.expected_outcome is not None


def test_full_example__includes_user_request_forbidden_outcome__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    assert hasattr(work_plan.user_request, "forbidden_outcome")
    assert work_plan.user_request.forbidden_outcome is not None


def test_full_example__includes_todo_parallel_field__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    assert len(work_plan.todos) > 0
    todo = work_plan.todos[0]
    assert hasattr(todo, "parallel")
    assert isinstance(todo.parallel, bool)


def test_full_example__includes_todo_parallelable_and_safe_evidence__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    assert len(work_plan.todos) > 0
    todo = work_plan.todos[0]
    assert hasattr(todo, "parallelable_and_safe_evidence")


def test_full_example__includes_todo_acceptance_criteria__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    assert len(work_plan.todos) > 0
    todo = work_plan.todos[0]
    assert hasattr(todo, "acceptance_criteria")
    assert isinstance(todo.acceptance_criteria, list)
    if len(todo.acceptance_criteria) > 0:
        acceptance = todo.acceptance_criteria[0]
        assert isinstance(acceptance, AcceptanceCriteriaItem)


def test_full_example__includes_verification_deterministic_bash__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    # Find a verification item with deterministic_bash
    for todo in work_plan.todos:
        for verif in todo.verification_spec:
            assert hasattr(verif, "deterministic_bash")
            assert isinstance(verif.deterministic_bash, list)
            if len(verif.deterministic_bash) > 0:
                bash_item = verif.deterministic_bash[0]
                assert isinstance(bash_item, DeterministicBashVerification)


def test_full_example__includes_verification_orchestrator_judge__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    # Find a verification item with orchestrator_judge
    for todo in work_plan.todos:
        for verif in todo.verification_spec:
            assert hasattr(verif, "orchestrator_judge")
            assert isinstance(verif.orchestrator_judge, list)


def test_full_example__includes_workplan_current_work_ids__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    assert hasattr(work_plan, "current_work_ids")
    assert isinstance(work_plan.current_work_ids, list)


def test_full_example__includes_workplan_acceptance_criteria_for_verification_agent__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    assert hasattr(work_plan, "acceptance_criteria_for_verification_agent")
    assert isinstance(work_plan.acceptance_criteria_for_verification_agent, list)


def test_full_example__includes_workplan_fully_done_evidence__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    assert hasattr(work_plan, "fully_done_evidence")


def test_full_example__includes_execution_status_fully_done_at__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    assert isinstance(work_plan.execution, ExecutionStatus)
    assert hasattr(work_plan.execution, "fully_done_at")


def test_full_example__returns_valid_plan_document__passes_validation() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    assert plan_doc.version == "3.0"
    assert len(plan_doc.work_plans) > 0
    # Verify metadata was updated with current timestamp
    assert plan_doc.metadata.created_at is not None
    assert plan_doc.metadata.updated_at is not None


def test_full_example__all_todos_have_new_fields__returns_document() -> None:
    # Given
    template_gen = PlanTemplateGenerator()

    # When
    plan_doc = template_gen.full_example()

    # Then
    assert isinstance(plan_doc, PlanDocument)
    work_plan = plan_doc.work_plans[0]
    for todo in work_plan.todos:
        # Verify all new fields exist
        assert hasattr(todo, "parallel")
        assert hasattr(todo, "parallelable_and_safe_evidence")
        assert hasattr(todo, "acceptance_criteria")
        assert isinstance(todo.acceptance_criteria, list)


def test_full_example_has_at_least_four_acceptance_criteria() -> None:
    """Given: PlanTemplateGenerator.full_example()
    When: 템플릿 생성
    Then: acceptance_criteria_for_verification_agent가 4개 이상
    """
    # Given/When
    doc = PlanTemplateGenerator.full_example()

    # Then
    plan = doc.work_plans[0]
    criteria = plan.acceptance_criteria_for_verification_agent

    assert len(criteria) >= 4, f"Expected >= 4, got {len(criteria)}"

    # 각 criteria가 최소 2개 checklist 포함하는지도 검증
    for criterion in criteria:
        assert len(criterion.checklists) >= 2, (
            f"Criterion {criterion.id} has {len(criterion.checklists)} checklists, expected >= 2"
        )
