import pytest

from sisyphus.core.plan_linter import PlanLinter
from sisyphus.core.plans.models import Metadata, PlanDocument, ReferenceItem, Todo, TodoStatus, WorkPlan

pytestmark = [pytest.mark.anyio]


def test_validate_references__if_valid_references__returns_empty() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[
                    Todo(
                        id="1",
                        title="Task 1",
                        status=TodoStatus.pending,
                        references=[ReferenceItem(ref_id="ref-1")],
                    )
                ],
                references=[ReferenceItem(ref_id="ref-1", uri="https://example.com")],
            )
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 0


def test_validate_references__if_duplicate_ref_id__reports_error() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[],
                references=[
                    ReferenceItem(ref_id="ref-1", uri="https://example.com"),
                    ReferenceItem(ref_id="ref-1", uri="https://other.com"),
                ],
            )
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 1
    assert "Duplicate ref_id found" in errors[0]
    assert "ref-1" in errors[0]


def test_validate_references__if_missing_ref_id__reports_error() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[
                    Todo(
                        id="1",
                        title="Task 1",
                        status=TodoStatus.pending,
                        references=[ReferenceItem(ref_id="nonexistent")],
                    )
                ],
                references=[ReferenceItem(ref_id="ref-1", uri="https://example.com")],
            )
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 1
    assert "nonexistent" in errors[0]
    assert "not defined in references section" in errors[0]


def test_validate_references__if_inline_too_long__reports_warning() -> None:
    # given
    long_inline = "x" * 600
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[],
                references=[ReferenceItem(ref_id="ref-1", inline=long_inline)],
            )
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 1
    assert "inline reference too long" in errors[0]
    assert "600 chars" in errors[0]
    assert "recommend < 500" in errors[0]
    assert "Plan A" in errors[0]


def test_validate_references__if_inline_exactly_500__no_warning() -> None:
    # given
    inline_500 = "x" * 500
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[],
                references=[ReferenceItem(ref_id="ref-1", inline=inline_500)],
            )
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 0


def test_validate_references__if_references_section_missing_ref_id__reports_error() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[],
                references=[ReferenceItem(ref_id=None, uri="https://example.com")],
            )
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 1
    assert "missing ref_id" in errors[0]
    assert "references section must have ref_id" in errors[0]


def test_validate_references__if_inline_only_in_todo__no_error() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[
                    Todo(
                        id="1",
                        title="Task 1",
                        status=TodoStatus.pending,
                        references=[ReferenceItem(inline="Inline text without ref_id")],
                    )
                ],
                references=[],
            )
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 0


def test_validate_references__if_nested_todo_refs__validates_recursively() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.pending,
                        children=[
                            Todo(
                                id="1.1",
                                title="Child",
                                status=TodoStatus.pending,
                                references=[ReferenceItem(ref_id="missing-ref")],
                            )
                        ],
                    )
                ],
                references=[ReferenceItem(ref_id="ref-1", uri="https://example.com")],
            )
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 1
    assert "missing-ref" in errors[0]


def test_validate_references__if_multiple_work_plans__validates_all() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                todos=[],
                references=[
                    ReferenceItem(ref_id="ref-1", uri="https://example.com"),
                    ReferenceItem(ref_id="ref-1", uri="https://duplicate.com"),
                ],
            ),
            WorkPlan(
                id="plan-b",
                name="Plan B",
                todos=[],
                references=[ReferenceItem(ref_id="ref-2", inline="x" * 600)],
            ),
        ],
    )
    linter = PlanLinter({})

    # when
    errors = linter.validate_references(plan_doc)

    # then
    assert len(errors) == 2
    assert any("Duplicate ref_id" in e for e in errors)
    assert any("inline reference too long" in e for e in errors)
