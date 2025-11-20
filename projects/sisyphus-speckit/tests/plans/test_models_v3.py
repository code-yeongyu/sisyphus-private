import pytest
from pydantic import ValidationError
from sisyphus_core.core.plans.models import (
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
    VerificationItem,
    Workflow,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_reference_item__if_uri_and_inline_both_provided__raises_error(
) -> None:
    # given
    data = {"uri": "https://example.com", "inline": "text content"}

    # when & then
    with pytest.raises(ValidationError) as exc:
        _ = ReferenceItem(**data)
    assert "uri와 inline은 동시에 사용할 수 없습니다" in str(exc.value)


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_reference_item__if_all_fields_none__raises_error(
) -> None:
    # given

    # when & then
    with pytest.raises(ValidationError) as exc:
        _ = ReferenceItem()
    assert "ref_id, uri 또는 inline 중 하나는 필수입니다" in str(exc.value)


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_reference_item__if_ref_id_only__creates_successfully(
) -> None:
    # given
    data = {"ref_id": "ref_123"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.ref_id == "ref_123"
    assert ref.uri is None
    assert ref.inline is None


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_reference_item__if_uri_only__creates_successfully(
) -> None:
    # given
    data = {"uri": "https://example.com"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.uri == "https://example.com"
    assert ref.ref_id is None
    assert ref.inline is None


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_reference_item__if_inline_only__creates_successfully(
) -> None:
    # given
    data = {"inline": "inline content"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.inline == "inline content"
    assert ref.ref_id is None
    assert ref.uri is None


async def test_work_plan__if_depends_on_provided__stores_dependency_list(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    data = {
        "id": "plan-1",
        "name": "Test Plan",
        "user_request": minimal_user_request.model_dump(),
        "objectives": minimal_objectives.model_dump(),
        "background": minimal_background.model_dump(),
        "required_background": minimal_required_background.model_dump(),
        "workflow": minimal_workflow.model_dump(),
        "success_vision": minimal_success_vision.model_dump(),
        "final_verification": [],
        "depends_on": ["plan-foundation", "plan-setup"],
        "todos": [],
    }

    # when
    plan = WorkPlan.model_validate(data)

    # then
    assert plan.depends_on == ["plan-foundation", "plan-setup"]


async def test_work_plan__if_depends_on_not_provided__defaults_to_empty_list(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    data = {
        "id": "plan-1",
        "name": "Test Plan",
        "user_request": minimal_user_request.model_dump(),
        "objectives": minimal_objectives.model_dump(),
        "background": minimal_background.model_dump(),
        "required_background": minimal_required_background.model_dump(),
        "workflow": minimal_workflow.model_dump(),
        "success_vision": minimal_success_vision.model_dump(),
        "final_verification": [],
        "todos": [],
    }

    # when
    plan = WorkPlan.model_validate(data)

    # then
    assert plan.depends_on == []


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_todo__if_description_provided__stores_description(
) -> None:
    # given
    data = {
        "id": "1",
        "title": "Test Task",
        "description": "Detailed task description",
        "status": TodoStatus.pending,
    }

    # when
    todo = Todo.model_validate(data)

    # then
    assert todo.description == "Detailed task description"


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_todo__if_description_not_provided__defaults_to_none(
) -> None:
    # given
    data = {"id": "1", "title": "Test Task", "status": TodoStatus.pending}

    # when
    todo = Todo.model_validate(data)

    # then
    assert todo.description is None


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_todo__if_children_provided__stores_nested_todos(
) -> None:
    # given
    child1 = Todo(id="1.1", title="Subtask 1", status=TodoStatus.pending)
    child2 = Todo(id="1.2", title="Subtask 2", status=TodoStatus.completed)
    parent_data = {
        "id": "1",
        "title": "Parent Task",
        "status": TodoStatus.in_progress,
        "children": [child1, child2],
    }

    # when
    parent = Todo.model_validate(parent_data)

    # then
    assert parent.children is not None
    assert len(parent.children) == 2
    assert parent.children[0].id == "1.1"
    assert parent.children[1].status == TodoStatus.completed


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_todo__if_children_not_provided__defaults_to_none(
) -> None:
    # given
    data = {"id": "1", "title": "Task", "status": TodoStatus.pending}

    # when
    todo = Todo.model_validate(data)

    # then
    assert todo.children is None


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_plan_document__if_valid_structure__creates_successfully(
) -> None:
    # given
    data = {
        "version": "3.0",
        "metadata": {"created_at": "2025-11-01T20:00:00Z"},
        "work_plans": [
            {
                "id": "plan-main",
                "name": "Main Plan",
                "depends_on": ["plan-foundation"],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task 1",
                        "description": "Description",
                        "status": "pending",
                    }
                ],
                "user_request": {
                    "original": "Test user request",
                    "created_at": "2025-11-06T00:00:00Z",
                    "additional": [],
                },
                "objectives": {"core": "Test objective", "detailed": []},
                "background": {
                    "current_situation": "Test situation",
                    "reason_for_change": "Test reason",
                    "changes_to_make": "Test changes",
                },
                "required_background": {
                    "description": "Test background",
                    "file_structure": None,
                    "references": [],
                },
                "workflow": {"dependency_diagram": "Test diagram", "critical_path": []},
                "success_vision": {
                    "user_perspective": [],
                    "business_perspective": [],
                    "technical_criteria": [],
                },
                "final_verification": [],
            }
        ],
    }

    # when
    doc = PlanDocument.model_validate(data)

    # then
    assert doc.version == "3.0"
    assert doc.metadata.created_at == "2025-11-01T20:00:00Z"
    assert len(doc.work_plans) == 1
    assert doc.work_plans[0].depends_on == ["plan-foundation"]


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_todo_status__if_enum_values__match_expected(
) -> None:
    # given & when & then
    assert TodoStatus.pending.value == "pending"
    assert TodoStatus.in_progress.value == "in_progress"
    assert TodoStatus.completed.value == "completed"
    assert TodoStatus.blocked.value == "blocked"


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_verification_item__if_all_fields_provided__creates_successfully(
) -> None:
    # given
    data = {
        "id": "ver_001",
        "title": "Test verification",
        "description": "Run tests",
        "orchestrator_manually_verified": False,
        "manual_verification_evidence": "",
        "bash": [{"execute": "pytest", "expected_exit_code": 0}],
    }

    # when
    ver = VerificationItem.model_validate(data)

    # then
    assert ver.id == "ver_001"
    assert ver.title == "Test verification"
    assert ver.description == "Run tests"
    assert len(ver.bash) == 1
    assert ver.bash[0].execute == "pytest"


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_reference_item__if_ref_id_and_uri__creates_successfully(
) -> None:
    # given
    data = {"ref_id": "ref_001", "uri": "https://example.com"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.ref_id == "ref_001"
    assert ref.uri == "https://example.com"
    assert ref.inline is None


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_reference_item__if_ref_id_and_inline__creates_successfully(
) -> None:
    # given
    data = {"ref_id": "ref_002", "inline": "Some inline text"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.ref_id == "ref_002"
    assert ref.inline == "Some inline text"
    assert ref.uri is None


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_todo__if_one_level_children__creates_successfully(
) -> None:
    # given
    child_data = {
        "id": "1.1",
        "title": "Child Task",
        "status": "pending",
        "children": None,
    }
    parent_data = {
        "id": "1",
        "title": "Parent Task",
        "status": "pending",
        "children": [child_data],
    }

    # when
    parent = Todo.model_validate(parent_data)

    # then
    assert parent.children is not None
    assert len(parent.children) == 1
    assert parent.children[0].id == "1.1"
    assert parent.children[0].children is None


@pytest.mark.usefixtures("minimal_background", "minimal_objectives", "minimal_required_background", "minimal_success_vision", "minimal_user_request", "minimal_workflow")
async def test_metadata__if_only_created_at__updated_at_defaults_to_none(
) -> None:
    # given
    data = {"created_at": "2025-11-01T20:00:00Z"}

    # when
    metadata = Metadata(**data)

    # then
    assert metadata.created_at == "2025-11-01T20:00:00Z"
    assert metadata.updated_at is None
