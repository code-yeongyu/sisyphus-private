import pytest
from pydantic import ValidationError

from sisyphus.utils.plan_types import (
    BashVerification,
    LLMJudgeVerification,
    ReferencePointer,
    Todo,
    VerificationItem,
    WorkPlan,
)

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

    # when
    todo = Todo(**data)

    # then
    assert todo.id == "1"
    assert isinstance(todo.id, str)


async def test_workplan_loads_from_dict() -> None:
    # given
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "created_at": "2025-01-01"},
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


async def test_verification_item_bash_only__creates_successfully() -> None:
    # given
    data = {
        "id": "v1",
        "title": "check file",
        "description": "check file exists",
        "orchestrator_manually_verified": False,
        "manual_verification_evidence": "",
        "bash": [{"execute": "ls -al", "expected_exit_code": 0}],
    }

    # when
    item = VerificationItem(**data)

    # then
    assert item.verified is False
    assert len(item.bash) == 1
    assert len(item.llm_judge) == 0
    assert item.bash[0].execute == "ls -al"


async def test_verification_item_llm_judge_only__creates_successfully() -> None:
    # given
    data = {
        "id": "v2",
        "title": "check with llm",
        "description": "llm judge verification",
        "orchestrator_manually_verified": False,
        "manual_verification_evidence": "",
        "llm_judge": [{"instruction": "check if file exists"}],
    }

    # when
    item = VerificationItem(**data)

    # then
    assert item.verified is False
    assert len(item.bash) == 0
    assert len(item.llm_judge) == 1
    assert item.llm_judge[0].instruction == "check if file exists"


async def test_verification_item_both_bash_and_llm__creates_successfully() -> None:
    # given
    data = {
        "id": "v3",
        "title": "both verification",
        "description": "both bash and llm",
        "orchestrator_manually_verified": False,
        "manual_verification_evidence": "",
        "bash": [{"execute": "ls"}],
        "llm_judge": [{"instruction": "check"}],
    }

    # when
    item = VerificationItem(**data)

    # then
    assert len(item.bash) == 1
    assert len(item.llm_judge) == 1


async def test_verification_item_neither_bash_nor_llm__raises_error() -> None:
    # given
    data = {
        "id": "v4",
        "title": "no verification",
        "description": "missing both",
        "orchestrator_manually_verified": False,
        "manual_verification_evidence": "",
    }

    # when & then
    with pytest.raises(ValidationError) as exc:
        VerificationItem(**data)
    assert "bash 또는 llm_judge 중 하나 이상 필수" in str(exc.value)


async def test_bash_verification__creates_with_all_fields() -> None:
    # given
    data = {
        "execute": "pytest",
        "expected_stdout": "passed",
        "expected_stderr": "",
        "expected_exit_code": 0,
        "notes": "run all tests",
    }

    # when
    bash = BashVerification(**data)

    # then
    assert bash.execute == "pytest"
    assert bash.expected_stdout == "passed"
    assert bash.notes == "run all tests"


async def test_llm_judge_verification__creates_with_context_commands() -> None:
    # given
    data = {
        "by": "orchestrator-agent",
        "context_commands": ["ls -al", "cat config.json"],
        "instruction": "verify config is correct",
    }

    # when
    llm = LLMJudgeVerification(**data)

    # then
    assert llm.by.value == "orchestrator-agent"
    assert len(llm.context_commands) == 2
    assert llm.instruction == "verify config is correct"


async def test_reference_pointer__creates_with_type_field() -> None:
    # given
    data = {"type": "pointer", "ref_id": "ref_001", "notes": "see reference"}

    # when
    ref = ReferencePointer(**data)  # type: ignore[arg-type]

    # then
    assert ref.type == "pointer"
    assert ref.ref_id == "ref_001"
    assert ref.notes == "see reference"


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


async def test_pydantic_validation_fails__when_invalid_status__raises_error() -> None:
    # given
    data = {
        "id": "1",
        "title": "Test",
        "status": "invalid_status",
        "created_at": "2025-01-01",
        "updated_at": "2025-01-01",
    }

    # when & then
    with pytest.raises(ValidationError) as exc:
        Todo(**data)  # type: ignore
    assert "status" in str(exc.value).lower()


async def test_pydantic_validation_fails__when_missing_required_field__raises_error() -> None:
    # given
    data = {
        "id": "1",
        "status": "pending",
        "created_at": "2025-01-01",
        "updated_at": "2025-01-01",
    }

    # when & then
    with pytest.raises(ValidationError) as exc:
        Todo(**data)  # type: ignore
    assert "title" in str(exc.value).lower()


async def test_workplan_validation_fails__when_missing_metadata__raises_error() -> None:
    # given
    data = {
        "user_request": {"original": "Test", "created_at": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
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

    # when & then
    with pytest.raises(ValidationError) as exc:
        WorkPlan(**data)  # type: ignore
    assert "metadata" in str(exc.value).lower()


async def test_verification_item_verified_defaults_to_false() -> None:
    # given
    data = {
        "id": "v5",
        "title": "default test",
        "description": "Test default values",
        "orchestrator_manually_verified": False,
        "manual_verification_evidence": "",
        "bash": [{"execute": "ls"}],
    }

    # when
    item = VerificationItem(**data)

    # then
    assert item.verified is False
    assert item.verified_at is None
    assert item.verification_evidence is None


async def test_verification_item_verified_can_be_set() -> None:
    # given
    data = {
        "id": "v6",
        "title": "verified test",
        "description": "Test setting verified",
        "verified": True,
        "verified_at": "2025-01-01T12:00:00",
        "verification_evidence": "test passed",
        "orchestrator_manually_verified": True,
        "manual_verification_evidence": "manually checked",
        "bash": [{"execute": "ls"}],
    }

    # when
    item = VerificationItem(**data)

    # then
    assert item.verified is True
    assert item.verified_at == "2025-01-01T12:00:00"
    assert item.verification_evidence == "test passed"
    assert item.orchestrator_manually_verified is True
    assert item.manual_verification_evidence == "manually checked"
