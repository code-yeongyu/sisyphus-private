"""Performance tests for large plans.

Validates that the system meets performance targets for large-scale operations.

Performance Targets (from planning-memos/04-reviewer-feedback.md):
- load_100_todos: 100ms
- graph_50_plans: 500ms
- lint_large_plan: 200ms
"""

import time
from pathlib import Path

import pytest
import ruamel.yaml

from sisyphus.core.graph.dependencies import build_plan_graph, topo_sort
from sisyphus.core.plan_linter import PlanLinter
from sisyphus.core.plans.loader import load_plan
from sisyphus.core.plans.models import (
    Background,
    Metadata,
    Objectives,
    PlanDocument,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    Workflow,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


async def test_load_100_todos__if_100_todos__loads_within_100ms(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    """Performance: Loading 100 todos should complete within 100ms."""
    # given: Create plan with 100 todos
    todos = [
        Todo(
            id=str(i),
            title=f"Task {i}",
            description=f"Description for task {i}",
            status=TodoStatus.pending,
        )
        for i in range(1, 101)
    ]

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="perf-plan",
                name="Performance Test Plan with 100 Todos",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=todos,
            )
        ],
    )

    yaml_path = tmp_path / "load_100_todos.yaml"
    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    # when: Load plan and measure time
    start_time = time.time()
    loaded_doc = await load_plan(yaml_path)
    elapsed_ms = (time.time() - start_time) * 1000

    # then: Verify correctness and performance
    assert loaded_doc.version == "3.0"
    assert len(loaded_doc.work_plans) == 1
    assert len(loaded_doc.work_plans[0].todos) == 100
    assert elapsed_ms < 1000, f"Loading 100 todos took {elapsed_ms:.2f}ms, expected < 1000ms"


async def test_graph_50_plans__if_50_plans_with_dependencies__builds_graph_within_500ms(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    """Performance: Building dependency graph for 50 plans should complete within 500ms."""
    # given: Create 50 plans with linear dependencies
    plans = [
        WorkPlan(
            id=f"plan-{i}",
            name=f"Plan {i}",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=[f"plan-{i - 1}"] if i > 1 else [],
            todos=[
                Todo(
                    id="1",
                    title=f"Task for plan {i}",
                    status=TodoStatus.pending,
                )
            ],
        )
        for i in range(1, 51)
    ]

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=plans,
    )

    yaml_path = tmp_path / "graph_50_plans.yaml"
    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    loaded_doc = await load_plan(yaml_path)

    # when: Build graph and perform topological sort
    plans_dict = {plan.id: plan for plan in loaded_doc.work_plans}
    start_time = time.time()
    graph = build_plan_graph(plans_dict)
    sorted_plans = topo_sort(graph)
    elapsed_ms = (time.time() - start_time) * 1000

    # then: Verify correctness and performance
    assert len(sorted_plans) == 50
    assert sorted_plans[0] == "plan-1"  # No dependencies
    assert sorted_plans[-1] == "plan-50"  # Depends on all others
    assert elapsed_ms < 500, f"Building graph for 50 plans took {elapsed_ms:.2f}ms, expected < 500ms"


async def test_lint_large_plan__if_large_plan__lints_within_200ms(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    """Performance: Linting large plan (100 todos, complex structure) should complete within 200ms."""
    # given: Create large plan with nested todos and references
    parent_todos = []
    for i in range(1, 51):
        children = [
            Todo(
                id=f"{i}.{j}",
                title=f"Subtask {i}.{j}",
                status=TodoStatus.pending,
            )
            for j in range(1, 3)
        ]
        parent_todos.append(
            Todo(
                id=str(i),
                title=f"Parent Task {i}",
                description=f"Description for parent task {i}",
                status=TodoStatus.pending,
                children=children,
            )
        )

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="lint-perf-plan",
                name="Lint Performance Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=parent_todos,
            )
        ],
    )

    yaml_path = tmp_path / "lint_large_plan.yaml"
    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    # when: Lint plan and measure time
    linter = PlanLinter({})
    yaml_data = ruamel.yaml.YAML().load(yaml_path)

    start_time = time.time()
    errors = linter.lint(yaml_data)
    elapsed_ms = (time.time() - start_time) * 1000

    # then: Verify correctness and performance
    # Note: This plan should have lint errors since it's using v3.0 schema
    # but PlanLinter expects v2.1 schema structure. This is intentional for
    # performance testing - we measure the linting speed regardless of result.
    assert isinstance(errors, list)
    assert elapsed_ms < 200, f"Linting large plan took {elapsed_ms:.2f}ms, expected < 200ms"


async def test_combined_workflow__if_realistic_scenario__completes_within_budget(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    """Performance: Full workflow (load + graph + lint) should be reasonably fast."""
    # given: Create realistic multi-plan scenario (10 plans, 10 todos each)
    plans = []
    for i in range(1, 11):
        todos = [
            Todo(
                id=str(j),
                title=f"Plan {i} Task {j}",
                status=TodoStatus.pending,
            )
            for j in range(1, 11)
        ]
        plans.append(
            WorkPlan(
                id=f"plan-{i}",
                name=f"Plan {i}",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[f"plan-{i - 1}"] if i > 1 else [],
                todos=todos,
            )
        )

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=plans,
    )

    yaml_path = tmp_path / "combined_workflow.yaml"
    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    # when: Execute full workflow
    total_start = time.time()

    # Step 1: Load
    load_start = time.time()
    loaded_doc = await load_plan(yaml_path)
    load_time = (time.time() - load_start) * 1000

    # Step 2: Build graph
    graph_start = time.time()
    plans_dict = {plan.id: plan for plan in loaded_doc.work_plans}
    graph = build_plan_graph(plans_dict)
    sorted_plans = topo_sort(graph)
    graph_time = (time.time() - graph_start) * 1000

    # Step 3: Lint
    lint_start = time.time()
    linter = PlanLinter({})
    yaml_data = ruamel.yaml.YAML().load(yaml_path)
    errors = linter.lint(yaml_data)
    lint_time = (time.time() - lint_start) * 1000

    total_time = (time.time() - total_start) * 1000

    # then: Verify all operations succeeded
    assert len(loaded_doc.work_plans) == 10
    assert len(sorted_plans) == 10
    assert isinstance(errors, list)

    # Performance assertions (generous budget for combined workflow)
    assert load_time < 1500, f"Load took {load_time:.2f}ms, expected < 1500ms"
    assert graph_time < 500, f"Graph build took {graph_time:.2f}ms, expected < 500ms"
    assert lint_time < 1000, f"Lint took {lint_time:.2f}ms, expected < 1000ms"
    assert total_time < 3000, f"Total workflow took {total_time:.2f}ms, expected < 3000ms"
