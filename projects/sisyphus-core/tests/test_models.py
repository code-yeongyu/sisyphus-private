from __future__ import annotations

import pytest
from pydantic import ValidationError

from sisyphus_core.core.plans.models import (
    BashVerification,
    ReferenceItem,
    Todo,
    TodoStatus,
    VerificationItem,
)

pytestmark = [pytest.mark.anyio]


async def test_todo__if_valid_data__creates_successfully() -> None:
    # given & when
    todo = Todo(id="1", title="Test Task", status=TodoStatus.pending)

    # then
    assert todo.id == "1"
    assert todo.title == "Test Task"
    assert todo.status == TodoStatus.pending


async def test_todo__if_with_description__stores_description() -> None:
    # given & when
    todo = Todo(id="1", title="Task", description="Detailed description", status=TodoStatus.pending)

    # then
    assert todo.description == "Detailed description"


async def test_todo_status__if_enum_values__match_expected() -> None:
    # given & when & then
    assert TodoStatus.pending.value == "pending"
    assert TodoStatus.in_progress.value == "in_progress"
    assert TodoStatus.completed.value == "completed"
    assert TodoStatus.blocked.value == "blocked"


async def test_reference_item__if_uri_only__creates_successfully() -> None:
    # given
    data = {"uri": "https://example.com"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.uri == "https://example.com"
    assert ref.inline is None


async def test_reference_item__if_inline_only__creates_successfully() -> None:
    # given
    data = {"inline": "inline text"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.inline == "inline text"
    assert ref.uri is None


async def test_reference_item__if_uri_and_inline__raises_error() -> None:
    # given
    data = {"uri": "https://example.com", "inline": "text"}

    # when & then
    with pytest.raises(ValidationError) as exc:
        ReferenceItem(**data)
    assert "uri와 inline은 동시에 사용할 수 없습니다" in str(exc.value)


async def test_verification_item__if_valid_bash__creates_successfully() -> None:
    # given
    bash_verification = BashVerification(execute="pytest", expected_exit_code=0)

    # when
    ver = VerificationItem(
        id="v1",
        title="Test verification",
        description="Run tests",
        verified=False,
        verified_at=None,
        verification_evidence=None,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[bash_verification],
        llm_judge=[],
    )

    # then
    assert ver.id == "v1"
    assert len(ver.bash) == 1
    assert ver.bash[0].execute == "pytest"
