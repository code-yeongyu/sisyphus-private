import time
from pathlib import Path

import pytest
import ruamel.yaml

from sisyphus.core.plans.loader import load_plan
from sisyphus.core.plans.models import (
    Background,
    Metadata,
    Objectives,
    PlanDocument,
    ReferenceItem,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    Workflow,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


async def test_large_yaml_hundreds_of_todos__if_200_todos__loads_successfully(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    todos = [
        Todo(
            id=str(i),
            title=f"Task {i}",
            description=f"Description for task {i}",
            status=TodoStatus.pending,
        )
        for i in range(1, 201)
    ]

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="large-plan",
                name="Large Plan with 200 Todos",
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

    yaml_path = tmp_path / "large.yaml"

    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    # when
    loaded_doc = await load_plan(yaml_path)

    # then
    assert loaded_doc.version == "3.0"
    assert len(loaded_doc.work_plans) == 1
    assert len(loaded_doc.work_plans[0].todos) == 200
    assert loaded_doc.work_plans[0].todos[0].id == "1"
    assert loaded_doc.work_plans[0].todos[199].id == "200"


async def test_large_yaml_nested_todos__if_deep_nesting__loads_successfully(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    parent_todos = []
    for i in range(1, 51):
        children = [
            Todo(
                id=f"{i}.{j}",
                title=f"Subtask {i}.{j}",
                status=TodoStatus.pending,
            )
            for j in range(1, 6)
        ]
        parent_todos.append(
            Todo(
                id=str(i),
                title=f"Parent Task {i}",
                status=TodoStatus.pending,
                children=children,
            )
        )

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="nested-plan",
                name="Nested Plan",
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

    yaml_path = tmp_path / "nested.yaml"

    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    # when
    loaded_doc = await load_plan(yaml_path)

    # then
    assert len(loaded_doc.work_plans[0].todos) == 50
    assert all(len(todo.children or []) == 5 for todo in loaded_doc.work_plans[0].todos)


async def test_large_yaml_many_plans__if_50_plans__loads_successfully(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
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

    yaml_path = tmp_path / "many_plans.yaml"

    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    # when
    loaded_doc = await load_plan(yaml_path)

    # then
    assert len(loaded_doc.work_plans) == 50
    assert loaded_doc.work_plans[0].depends_on == []
    assert loaded_doc.work_plans[1].depends_on == ["plan-1"]
    assert loaded_doc.work_plans[49].depends_on == ["plan-49"]


async def test_large_yaml_many_references__if_100_references__loads_successfully(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given

    references = [
        ReferenceItem(
            ref_id=f"ref_{i}",
            uri=f"https://example.com/doc/{i}",
        )
        for i in range(1, 101)
    ]

    todos = [
        Todo(
            id="1",
            title="Task with many references",
            status=TodoStatus.pending,
            references=[ReferenceItem(ref_id=f"ref_{i}") for i in range(1, 101)],
        )
    ]

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="ref-heavy-plan",
                name="Reference Heavy Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=todos,
                references=references,
            )
        ],
    )

    yaml_path = tmp_path / "many_refs.yaml"

    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    # when
    loaded_doc = await load_plan(yaml_path)

    # then
    assert len(loaded_doc.work_plans[0].references) == 100
    assert len(loaded_doc.work_plans[0].todos[0].references) == 100


async def test_large_yaml_performance__if_large_file__loads_within_reasonable_time(
    tmp_path: Path,
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given

    todos = [
        Todo(
            id=str(i),
            title=f"Task {i}",
            description=f"Long description for task {i} " * 10,
            status=TodoStatus.pending,
        )
        for i in range(1, 301)
    ]

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="perf-test",
                name="Performance Test Plan",
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

    yaml_path = tmp_path / "performance.yaml"

    yaml = ruamel.yaml.YAML()
    with open(yaml_path, "w") as f:  # noqa: ASYNC230
        yaml.dump(plan_doc.model_dump(mode="json"), f)

    # when
    start_time = time.time()
    loaded_doc = await load_plan(yaml_path)
    elapsed_time = time.time() - start_time

    # then
    assert loaded_doc.version == "3.0"
    assert len(loaded_doc.work_plans[0].todos) == 300
    assert elapsed_time < 1.0
