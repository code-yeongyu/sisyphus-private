from pathlib import Path

import pytest
from sisyphus_core.core.graph.dependencies import build_plan_graph, detect_cycles
from sisyphus_core.core.plan_linter import PlanLinter
from sisyphus_core.core.plans.models import (
    Background,
    Metadata,
    Objectives,
    PlanDocument,
    RequiredBackground,
    SuccessVision,
    UserRequest,
    Workflow,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


async def test_circular_dependency_two_nodes__if_a_depends_b_depends_a__detects_cycle(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-b"],
                todos=[],
            ),
            WorkPlan(
                id="plan-b",
                name="Plan B",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-a"],
                todos=[],
            ),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/circular-2.yaml")

    # when
    errors = linter.validate_depends_on(plan_doc, plan_path)

    # then
    assert len(errors) >= 1
    assert any("Circular dependency detected" in e for e in errors)
    assert any("plan-a" in e and "plan-b" in e for e in errors)


async def test_circular_dependency_three_nodes__if_a_b_c_cycle__detects_all_nodes(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-b"],
                todos=[],
            ),
            WorkPlan(
                id="plan-b",
                name="Plan B",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-c"],
                todos=[],
            ),
            WorkPlan(
                id="plan-c",
                name="Plan C",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-a"],
                todos=[],
            ),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/circular-3.yaml")

    # when
    errors = linter.validate_depends_on(plan_doc, plan_path)

    # then
    assert len(errors) >= 1
    cycle_error = [e for e in errors if "Circular dependency detected" in e][0]
    assert "plan-a" in cycle_error
    assert "plan-b" in cycle_error
    assert "plan-c" in cycle_error


async def test_circular_dependency_with_independent_plans__if_cycle_exists_separately__detects_only_cycle(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-x",
                name="Plan X",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-y"],
                todos=[],
            ),
            WorkPlan(
                id="plan-y",
                name="Plan Y",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-x"],
                todos=[],
            ),
            WorkPlan(
                id="plan-z",
                name="Plan Z",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            ),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/mixed-cycle.yaml")

    # when
    errors = linter.validate_depends_on(plan_doc, plan_path)

    # then
    assert len(errors) >= 1
    cycle_errors = [e for e in errors if "Circular dependency detected" in e]
    assert len(cycle_errors) >= 1
    assert any("plan-x" in e and "plan-y" in e for e in cycle_errors)


async def test_circular_dependency_complex__if_long_chain_with_cycle__detects_cycle(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    plans = {
        "plan-a": WorkPlan(
            id="plan-a",
            name="Plan A",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-b"],
            todos=[],
        ),
        "plan-b": WorkPlan(
            id="plan-b",
            name="Plan B",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-c"],
            todos=[],
        ),
        "plan-c": WorkPlan(
            id="plan-c",
            name="Plan C",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-d"],
            todos=[],
        ),
        "plan-d": WorkPlan(
            id="plan-d",
            name="Plan D",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-b"],
            todos=[],
        ),
    }
    graph = build_plan_graph(plans)

    # when
    cycles = detect_cycles(graph)

    # then
    assert len(cycles) >= 1
    cycle = cycles[0]
    assert "plan-b" in cycle
    assert "plan-c" in cycle
    assert "plan-d" in cycle


async def test_circular_dependency_multiple_cycles__if_two_separate_cycles__detects_both(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    plans = {
        "plan-a": WorkPlan(
            id="plan-a",
            name="Plan A",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-b"],
            todos=[],
        ),
        "plan-b": WorkPlan(
            id="plan-b",
            name="Plan B",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-a"],
            todos=[],
        ),
        "plan-x": WorkPlan(
            id="plan-x",
            name="Plan X",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-y"],
            todos=[],
        ),
        "plan-y": WorkPlan(
            id="plan-y",
            name="Plan Y",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-z"],
            todos=[],
        ),
        "plan-z": WorkPlan(
            id="plan-z",
            name="Plan Z",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-x"],
            todos=[],
        ),
    }
    graph = build_plan_graph(plans)

    # when
    cycles = detect_cycles(graph)

    # then
    assert len(cycles) == 2
    cycle_nodes = [set(cycle) for cycle in cycles]
    assert any({"plan-a", "plan-b"}.issubset(nodes) for nodes in cycle_nodes)
    assert any({"plan-x", "plan-y", "plan-z"}.issubset(nodes) for nodes in cycle_nodes)
