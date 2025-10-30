"""PlanLinter unit tests."""

import pytest

from sisyphus.core.plan_linter import LintError, PlanLinter

pytestmark = [pytest.mark.anyio]


async def test_lint_valid_yaml__when_all_fields_present__returns_no_errors() -> None:
    # given
    linter = PlanLinter({})
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
    errors = linter.lint(data)

    # then
    assert len(errors) == 0


async def test_lint_missing_required_field__when_metadata_missing__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) > 0
    assert any(e.location == "metadata" for e in errors)
    assert any("Missing required field" in e.message for e in errors)


async def test_lint_missing_nested_required_field__when_metadata_updated_at_missing__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01"},  # missing updated_at
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("metadata.updated_at" in e.location for e in errors)
    assert any("Missing required field" in e.message for e in errors)


async def test_lint_type_mismatch__when_boolean_is_string__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": "true", "completed": False},  # string, not boolean
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("status.execution.started" in e.location for e in errors)
    assert any("Type mismatch" in e.message for e in errors)


async def test_lint_extra_field__when_unknown_field_at_root__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [],
        "success_vision": {},
        "final_verification": [],
        "unknown_field": "value",  # not in schema
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("unknown_field" in e.location for e in errors)
    assert any("Unknown field" in e.message for e in errors)


async def test_lint_invalid_enum__when_todo_status_invalid__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [
            {
                "id": "1",
                "title": "Task",
                "status": "invalid_status",  # invalid enum value
                "created_at": "2025-01-01",
                "updated_at": "2025-01-01",
            }
        ],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("todos[0].status" in e.location for e in errors)
    assert any("Invalid enum" in e.message for e in errors)


async def test_lint_pattern_mismatch__when_todo_id_invalid__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [
            {
                "id": "abc",  # invalid pattern
                "title": "Task",
                "status": "pending",
                "created_at": "2025-01-01",
                "updated_at": "2025-01-01",
            }
        ],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("todos[0].id" in e.location for e in errors)
    assert any("Pattern mismatch" in e.message for e in errors)


async def test_lint_ref_integrity__when_ref_id_not_found__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {
            "description": "Test",
            "references": [
                {"type": "file", "path": "a.py", "description": "A"},
            ],
        },
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [
            {
                "id": "1",
                "title": "Task",
                "status": "pending",
                "created_at": "2025-01-01",
                "updated_at": "2025-01-01",
                "references": [{"ref_id": "nonexistent"}],  # Invalid ref_id
            }
        ],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("ref_id" in e.location for e in errors)
    assert any("not found" in e.message.lower() for e in errors)


async def test_lint_multiple_errors__when_multiple_issues__returns_all_errors() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01"},  # missing updated_at
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": "true", "completed": False},  # type error
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [
            {
                "id": "1",
                "title": "Task",
                "status": "invalid",  # enum error
                "created_at": "2025-01-01",
                "updated_at": "2025-01-01",
            }
        ],
        "success_vision": {},
        "final_verification": [],
        "extra_field": "value",  # extra field error
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) >= 4  # At least 4 errors
    assert any("metadata.updated_at" in e.location for e in errors)
    assert any("status.execution.started" in e.location for e in errors)
    assert any("todos[0].status" in e.location for e in errors)
    assert any("extra_field" in e.location for e in errors)


async def test_lint_recursive_children__when_child_has_error__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {"description": "Test"},
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [
            {
                "id": "1",
                "title": "Parent",
                "status": "pending",
                "created_at": "2025-01-01",
                "updated_at": "2025-01-01",
                "children": [
                    {
                        "id": "1.1",
                        "title": "Child",
                        "status": "invalid_status",  # error in child
                        "created_at": "2025-01-01",
                        "updated_at": "2025-01-01",
                    }
                ],
            }
        ],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("todos[0].children[0].status" in e.location for e in errors)
    assert any("Invalid enum" in e.message for e in errors)


async def test_lint_discriminated_union__when_type_field_missing__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data = {
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "user_request": {"original": "Test", "timestamp": "2025-01-01"},
        "objectives": {"core": "Test"},
        "background": {"current_situation": "A", "reason_for_change": "B", "changes_to_make": "C"},
        "required_background": {
            "description": "Test",
            "references": [
                {"path": "a.py", "description": "A"}  # missing 'type' field
            ],
        },
        "status": {
            "execution": {"started": False, "completed": False},
            "work_mode": {"parallel_requested": False},
            "progress": {"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0},
            "current_work": "None",
        },
        "workflow": {"dependency_diagram": "Test"},
        "todos": [],
        "success_vision": {},
        "final_verification": [],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("required_background.references[0].type" in e.location for e in errors)
    assert any("Missing required field" in e.message for e in errors)


async def test_format_error__when_all_fields_present__returns_formatted_message() -> None:
    # given
    linter = PlanLinter({})
    error = LintError(
        location="todos[0].status",
        message="Invalid enum value",
        expected="one of ['pending', 'in_progress', 'completed']",
        actual="invalid",
        suggestion="Change to one of: pending, in_progress, completed",
    )

    # when
    formatted = linter.format_error(error)

    # then
    assert "Error: todos[0].status - Invalid enum value" in formatted
    assert "Expected: one of ['pending', 'in_progress', 'completed']" in formatted
    assert "Actual: invalid" in formatted
    assert "Suggestion: Change to one of: pending, in_progress, completed" in formatted


async def test_format_error__when_optional_fields_missing__returns_minimal_message() -> None:
    # given
    linter = PlanLinter({})
    error = LintError(
        location="metadata",
        message="Missing required field",
    )

    # when
    formatted = linter.format_error(error)

    # then
    assert formatted == "Error: metadata - Missing required field"
