from __future__ import annotations

import pytest

from sisyphus.core.exporters.markdown import MarkdownExporter
from sisyphus.core.plans.models import (
    Metadata,
    PlanDocument,
    ReferenceItem,
    Todo,
    TodoStatus,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


async def test_export__with_single_todo__creates_checkbox() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Test Plan",
                todos=[Todo(id="1", title="Task 1", status=TodoStatus.pending)],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "# 사용자의 최초 요청" in result
    assert "Test Plan" in result
    assert "# TODOs" in result
    assert "- [ ] 1. Task 1" in result


async def test_export__with_completed_todo__creates_checked_checkbox() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Test",
                todos=[Todo(id="1", title="Done", status=TodoStatus.completed)],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "- [x] 1. Done" in result


async def test_export__with_children__indents_properly() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Test",
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.pending,
                        children=[Todo(id="1.1", title="Child", status=TodoStatus.completed)],
                    )
                ],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "- [ ] 1. Parent" in result
    assert "   - [x] 1.1. Child" in result


async def test_export__with_uri_references__creates_references_section() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Test",
                todos=[Todo(id="1", title="Task", status=TodoStatus.pending)],
                references=[ReferenceItem(ref_id="ref1", uri="https://example.com")],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "## References" in result
    assert "- [ref1]: https://example.com" in result


async def test_export__with_inline_references__creates_references_section() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Test",
                todos=[Todo(id="1", title="Task", status=TodoStatus.pending)],
                references=[ReferenceItem(ref_id="ref1", inline="Inline text here")],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "## References" in result
    assert "- [ref1]: Inline text here" in result


async def test_export__with_no_references__omits_references_section() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Test",
                todos=[Todo(id="1", title="Task", status=TodoStatus.pending)],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "## References" not in result


async def test_export__with_multiple_work_plans__combines_todos() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="First Plan",
                todos=[Todo(id="1", title="Task 1", status=TodoStatus.pending)],
            ),
            WorkPlan(
                id="plan-2",
                name="Second Plan",
                todos=[Todo(id="2", title="Task 2", status=TodoStatus.completed)],
            ),
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "First Plan" in result
    assert "Second Plan" in result
    assert "- [ ] 1. Task 1" in result
    assert "- [x] 2. Task 2" in result


async def test_export__with_nested_children__indents_multiple_levels() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Test",
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.pending,
                        children=[
                            Todo(
                                id="1.1",
                                title="Child",
                                status=TodoStatus.in_progress,
                                children=[
                                    Todo(
                                        id="1.1.1",
                                        title="Grandchild",
                                        status=TodoStatus.completed,
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "- [ ] 1. Parent" in result
    assert "   - [ ] 1.1. Child" in result
    assert "      - [x] 1.1.1. Grandchild" in result


async def test_export__with_multiple_references__lists_all() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Test",
                todos=[Todo(id="1", title="Task", status=TodoStatus.pending)],
                references=[
                    ReferenceItem(ref_id="ref1", uri="https://example.com"),
                    ReferenceItem(ref_id="ref2", inline="Some inline text"),
                    ReferenceItem(ref_id="ref3", uri="file:///path/to/file"),
                ],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "- [ref1]: https://example.com" in result
    assert "- [ref2]: Some inline text" in result
    assert "- [ref3]: file:///path/to/file" in result


async def test_export__with_empty_todos__creates_structure() -> None:
    # Given
    plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1",
                name="Empty Plan",
                todos=[],
            )
        ],
    )

    # When
    result = MarkdownExporter.export(plan)

    # Then
    assert "# 사용자의 최초 요청" in result
    assert "Empty Plan" in result
    assert "# TODOs" in result
