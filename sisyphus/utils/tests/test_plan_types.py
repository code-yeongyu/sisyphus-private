import pytest
from pydantic import ValidationError

from sisyphus.utils.plan_types import CommandInput, ProgrammaticVerify, Todo, WorkPlan

pytestmark = [pytest.mark.anyio]


async def test_todo_id_must_be_string() -> None:
    # given
    data = {
        "id": 1,
        "title": "Test",
        "status": "pending",
        "created_at": "2025-01-01",
        "updated_at": "2025-01-01",
    }

    # when & then
    with pytest.raises(ValidationError) as exc:
        Todo(**data)
    assert "id" in str(exc.value)


async def test_workplan_loads_from_dict() -> None:
    # given
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test objective"},
        "background": {
            "current_situation": "A",
            "reason_for_change": "B",
            "changes_to_make": "C",
        },
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False, "current_task_id": None},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    plan = WorkPlan(**data)

    # then
    assert plan.metadata.format_version == "2.0"
    assert plan.objectives.core == "Test objective"


async def test_discriminated_union_input() -> None:
    # given
    command_data = {"type": "command", "command": "ls"}

    # when
    input_spec = CommandInput(**command_data)  # pyright: ignore[reportArgumentType]

    # then
    assert input_spec.type == "command"
    assert input_spec.command == "ls"
    assert input_spec.capture_output is True


async def test_discriminated_union_verify() -> None:
    # given
    verify_data = {"type": "programmatic", "method": "contains", "expected": "OK"}

    # when
    verify_spec = ProgrammaticVerify(**verify_data)  # pyright: ignore[reportArgumentType]

    # then
    assert verify_spec.type == "programmatic"
    assert verify_spec.method == "contains"
    assert verify_spec.expected == "OK"


async def test_todo_recursive_children() -> None:
    # given
    child_data = {
        "id": "1.1",
        "title": "Child",
        "status": "pending",
        "created_at": "2025-01-01",
        "updated_at": "2025-01-01",
        "children": [],
    }
    parent_data = {
        "id": "1",
        "title": "Parent",
        "status": "pending",
        "created_at": "2025-01-01",
        "updated_at": "2025-01-01",
        "children": [child_data],
    }

    # when
    parent = Todo(**parent_data)

    # then
    assert len(parent.children) == 1
    assert parent.children[0].id == "1.1"
    assert parent.children[0].title == "Child"
