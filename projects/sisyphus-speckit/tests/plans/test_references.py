from __future__ import annotations

import pytest

from sisyphus_core.core.plans.models import (
    Background,
    Objectives,
    ReferenceItem,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    Workflow,
    WorkPlan,
)
from sisyphus_core.core.plans.references import ReferenceResolver

pytestmark = [pytest.mark.anyio]


async def test_index_references__with_valid_references__builds_index(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[
            ReferenceItem(ref_id="ref1", uri="https://example.com"),
            ReferenceItem(ref_id="ref2", inline="Inline content"),
        ],
    )

    # When
    index = ReferenceResolver.index_references(work_plan)

    # Then
    assert len(index) == 2
    assert "ref1" in index
    assert "ref2" in index
    assert index["ref1"].uri == "https://example.com"
    assert index["ref2"].inline == "Inline content"


async def test_index_references__with_duplicate_ref_id__raises_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[
            ReferenceItem(ref_id="ref1", uri="https://example.com"),
            ReferenceItem(ref_id="ref1", inline="Duplicate"),
        ],
    )

    # When / Then
    with pytest.raises(ValueError, match="Duplicate ref_id found: ref1"):
        ReferenceResolver.index_references(work_plan)


async def test_index_references__with_none_ref_id__skips_item(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[
            ReferenceItem(ref_id="ref1", uri="https://example.com"),
            ReferenceItem(uri="https://example2.com"),
        ],
    )

    # When
    index = ReferenceResolver.index_references(work_plan)

    # Then
    assert len(index) == 1
    assert "ref1" in index


async def test_index_references__with_empty_references__returns_empty_dict(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[],
    )

    # When
    index = ReferenceResolver.index_references(work_plan)

    # Then
    assert len(index) == 0


async def test_resolve_ref_id__with_existing_ref_id__returns_reference(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    index = {
        "ref1": ReferenceItem(ref_id="ref1", uri="https://example.com"),
        "ref2": ReferenceItem(ref_id="ref2", inline="Content"),
    }

    # When
    ref_item = ReferenceResolver.resolve_ref_id("ref1", index)

    # Then
    assert ref_item.ref_id == "ref1"
    assert ref_item.uri == "https://example.com"


async def test_resolve_ref_id__with_missing_ref_id__raises_key_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    index = {"ref1": ReferenceItem(ref_id="ref1", uri="https://example.com")}

    # When / Then
    with pytest.raises(KeyError, match="Reference ID 'ref99' not found"):
        ReferenceResolver.resolve_ref_id("ref99", index)


async def test_validate_references__with_valid_plan__returns_no_errors(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[
            Todo(
                id="1",
                title="Task 1",
                status=TodoStatus.pending,
                references=[ReferenceItem(ref_id="ref1")],
            )
        ],
        references=[ReferenceItem(ref_id="ref1", uri="https://example.com")],
    )

    # When
    errors = ReferenceResolver.validate_references(work_plan)

    # Then
    assert len(errors) == 0


async def test_validate_references__with_duplicate_ref_ids__returns_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[
            ReferenceItem(ref_id="ref1", uri="https://example.com"),
            ReferenceItem(ref_id="ref1", inline="Duplicate"),
        ],
    )

    # When
    errors = ReferenceResolver.validate_references(work_plan)

    # Then
    assert len(errors) == 1
    assert "Duplicate ref_id found: ref1" in errors[0]


async def test_validate_references__with_missing_ref_id_in_references__returns_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[
            ReferenceItem(ref_id="ref1", uri="https://example.com"),
            ReferenceItem(uri="https://example2.com"),
        ],
    )

    # When
    errors = ReferenceResolver.validate_references(work_plan)

    # Then
    assert len(errors) == 1
    assert "WorkPlan.references[1] missing ref_id" in errors[0]


async def test_validate_references__with_undefined_ref_id_used_in_todos__returns_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[
            Todo(
                id="1",
                title="Task 1",
                status=TodoStatus.pending,
                references=[ReferenceItem(ref_id="ref99")],
            )
        ],
        references=[ReferenceItem(ref_id="ref1", uri="https://example.com")],
    )

    # When
    errors = ReferenceResolver.validate_references(work_plan)

    # Then
    assert len(errors) == 1
    assert "Reference ID 'ref99' used in todos but not defined" in errors[0]


async def test_validate_references__with_nested_todos__validates_all_references(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[
            Todo(
                id="1",
                title="Parent Task",
                status=TodoStatus.pending,
                references=[ReferenceItem(ref_id="ref1")],
                children=[
                    Todo(
                        id="1.1",
                        title="Child Task",
                        status=TodoStatus.pending,
                        references=[ReferenceItem(ref_id="ref2")],
                    )
                ],
            )
        ],
        references=[
            ReferenceItem(ref_id="ref1", uri="https://example.com"),
            ReferenceItem(ref_id="ref2", inline="Child content"),
        ],
    )

    # When
    errors = ReferenceResolver.validate_references(work_plan)

    # Then
    assert len(errors) == 0


async def test_validate_references__with_nested_todos_missing_ref__returns_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[
            Todo(
                id="1",
                title="Parent Task",
                status=TodoStatus.pending,
                children=[
                    Todo(
                        id="1.1",
                        title="Child Task",
                        status=TodoStatus.pending,
                        references=[ReferenceItem(ref_id="ref99")],
                    )
                ],
            )
        ],
        references=[ReferenceItem(ref_id="ref1", uri="https://example.com")],
    )

    # When
    errors = ReferenceResolver.validate_references(work_plan)

    # Then
    assert len(errors) == 1
    assert "Reference ID 'ref99' used in todos but not defined" in errors[0]


async def test_validate_references__with_inline_reference_in_todos__no_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[
            Todo(
                id="1",
                title="Task 1",
                status=TodoStatus.pending,
                references=[ReferenceItem(inline="Direct inline content")],
            )
        ],
        references=[],
    )

    # When
    errors = ReferenceResolver.validate_references(work_plan)

    # Then
    assert len(errors) == 0


async def test_validate_references__with_multiple_errors__returns_all_errors(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # Given
    work_plan = WorkPlan(
        id="plan-test",
        name="Test Plan",
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[
            Todo(
                id="1",
                title="Task 1",
                status=TodoStatus.pending,
                references=[ReferenceItem(ref_id="ref99")],
            )
        ],
        references=[
            ReferenceItem(ref_id="ref1", uri="https://example.com"),
            ReferenceItem(ref_id="ref1", inline="Duplicate"),
            ReferenceItem(uri="https://no-id.com"),
        ],
    )

    # When
    errors = ReferenceResolver.validate_references(work_plan)

    # Then
    assert len(errors) == 3
    assert any("Duplicate ref_id found: ref1" in err for err in errors)
    assert any("WorkPlan.references[2] missing ref_id" in err for err in errors)
    assert any("Reference ID 'ref99' used in todos but not defined" in err for err in errors)
