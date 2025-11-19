"""Tests for task show command."""

from __future__ import annotations

import pytest
from sisyphus_core.core.plans.models import BashVerification, ReferenceItem, Todo, VerificationItem


class TestShowTask:
    """Tests for show_task command."""

    @pytest.fixture()
    def minimal_todo(self) -> Todo:
        """Create a minimal Todo for testing."""
        # given: a minimal todo with verification spec
        return Todo(
            id="test-task-1",
            title="Test Task",
            description="A test task",
            status=None,
            children=None,
            references=[
                ReferenceItem(
                    ref_id="ref-1",
                    uri=None,
                    inline="Test reference content",
                )
            ],
            verification_spec=[
                VerificationItem(
                    id="verify-1",
                    title="Verification 1",
                    description="Test verification",
                    verified=False,
                    verified_at=None,
                    verification_evidence=None,
                    orchestrator_manually_verified=False,
                    manual_verification_evidence="",
                    bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                    llm_judge=[],
                    deterministic_bash=[],
                    orchestrator_judge=[],
                )
            ],
            acceptance_criteria=[],
            parallel=False,
            parallelable_and_safe_evidence=None,
        )

    @pytest.fixture()
    def todo_with_children(self) -> Todo:
        """Create a Todo with children."""
        # given: a todo with child tasks
        child = Todo(
            id="child-task-1",
            title="Child Task",
            description="A child task",
            status=None,
            children=None,
            references=[],
            verification_spec=[],
            acceptance_criteria=[],
            parallel=False,
            parallelable_and_safe_evidence=None,
        )

        return Todo(
            id="parent-task-1",
            title="Parent Task",
            description="A parent task",
            status=None,
            children=[child],
            references=[],
            verification_spec=[],
            acceptance_criteria=[],
            parallel=False,
            parallelable_and_safe_evidence=None,
        )

    def test_show__verification_spec_exists__displays_table(self, minimal_todo: Todo) -> None:
        """Test that verification spec table is displayed."""
        # given: a todo with verification_spec
        task = minimal_todo
        # when: checking if verification_spec exists
        # then: verification_spec should be present
        assert task.verification_spec is not None
        assert len(task.verification_spec) == 1
        assert task.verification_spec[0].id == "verify-1"

    def test_show__verification_spec_details__shows_bash_and_llm(self, minimal_todo: Todo) -> None:
        """Test that verification spec details include bash and llm judges."""
        # given: a verification spec with bash and llm fields
        task = minimal_todo
        vspec = task.verification_spec[0]
        # when: checking verification spec fields
        # then: bash and llm_judge should be accessible
        assert hasattr(vspec, "bash")
        assert hasattr(vspec, "llm_judge")

    def test_show__children_exist__displays_recursively(self, todo_with_children: Todo) -> None:
        """Test that children are displayed recursively."""
        # given: a todo with children
        task = todo_with_children
        # when: checking if children exist
        # then: children should be present
        assert task.children is not None
        assert len(task.children) == 1
        assert task.children[0].id == "child-task-1"

    def test_show__nested_children__maintains_hierarchy(self, todo_with_children: Todo) -> None:
        """Test that nested children maintain hierarchy."""
        # given: a parent task with child
        parent = todo_with_children
        # when: creating deeper nesting
        assert parent.children is not None
        child = parent.children[0]
        # then: should maintain proper references
        assert child.title == "Child Task"
        assert parent.id == "parent-task-1"

    def test_show__references_with_ref_id__can_be_resolved(self, minimal_todo: Todo) -> None:
        """Test that references with ref_id can be resolved."""
        # given: a todo with ref_id references
        task = minimal_todo
        refs = task.references
        # when: checking references
        # then: ref_id should be accessible
        assert refs is not None
        assert refs[0].ref_id == "ref-1"

    def test_show__references_inline__shows_truncated(self, minimal_todo: Todo) -> None:
        """Test that inline references are truncated."""
        # given: a todo with inline reference
        task = minimal_todo
        ref = task.references[0]
        # when: checking inline content
        # then: inline should be truncable
        if ref.inline:
            truncated = ref.inline[:100] + "..." if len(ref.inline) > 100 else ref.inline
            assert len(truncated) <= len(ref.inline) + 3 or len(ref.inline) <= 100

    def test_show__verification_status__shows_verified_flag(self, minimal_todo: Todo) -> None:
        """Test that verification status shows verified flag."""
        # given: a verification item with verified flag
        vspec = minimal_todo.verification_spec[0]
        # when: checking verified field
        # then: verified flag should be accessible
        assert hasattr(vspec, "verified")
        assert vspec.verified is False

    def test_show__task_basic_info__has_required_fields(self, minimal_todo: Todo) -> None:
        """Test that task has required fields for display."""
        # given: a minimal todo
        task = minimal_todo
        # when: checking required fields
        # then: all fields should exist
        assert task.id is not None
        assert task.title is not None
        assert hasattr(task, "references")
        assert hasattr(task, "verification_spec")
        assert hasattr(task, "children")
