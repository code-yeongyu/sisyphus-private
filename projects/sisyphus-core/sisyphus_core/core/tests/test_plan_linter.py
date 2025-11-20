"""PlanLinter unit tests."""

from pathlib import Path
from typing import Any

import pytest

from sisyphus_core.core.plan_linter import LintError, PlanLinter
from sisyphus_core.core.plans.models import PlanDocument

pytestmark = [pytest.mark.anyio]


async def test_lint_valid_yaml__when_all_fields_present__returns_no_errors() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "plan-1",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01"},
                "objectives": {"core": "Test objective"},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test"},
                "workflow": {"dependency_diagram": "Test"},
                "todos": [
                    {
                        "id": "1",
                        "title": "Test task",
                        "status": "pending",
                        "references": [],
                        "verification_spec": [],
                    }
                ],
                "success_vision": {},
                "final_verification": [],
                "execution": {"started": False, "completed": False},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "None",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) == 0


async def test_lint_missing_required_field__when_metadata_missing__returns_error() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure - missing metadata to trigger error
    data: dict[str, Any] = {
        "version": "3.0",
        # metadata is missing
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01T00:00:00Z", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) > 0
    assert any(e.location == "metadata" for e in errors)
    assert any("Missing required field" in e.message for e in errors)


async def test_lint_type_mismatch__when_boolean_is_string__returns_error() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test request", "created_at": "2025-01-01T00:00:00Z", "additional": []},
                "objectives": {"core": "Test objective", "detailed": []},
                "background": {
                    "current_situation": "Test",
                    "reason_for_change": "Test",
                    "changes_to_make": "Test",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [],
                "execution": {
                    "started": "true",  # string, not boolean - type error
                    "completed": False,
                    "started_at": None,
                    "completed_at": None,
                },
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("work_plans[0].execution.started" in e.location for e in errors)
    assert any("Type mismatch" in e.message for e in errors)


async def test_lint_extra_field__when_unknown_field_at_root__returns_error() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
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
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "invalid_status",  # invalid enum value
                        "references": [],
                        "verification_spec": [],
                    }
                ],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("work_plans[0].todos[0].status" in e.location for e in errors)
    assert any("Invalid enum" in e.message for e in errors)


async def test_lint_ref_integrity__when_ref_id_not_found__returns_error() -> None:
    # given
    linter = PlanLinter({})
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {
                    "description": "Test",
                    "file_structure": None,
                    "references": [
                        {"ref_id": "ref1", "uri": "file://a.py"},
                    ],
                },
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "pending",
                        "references": [{"ref_id": "nonexistent"}],
                        "verification_spec": [],
                    }
                ],
                "references": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    plan_doc = PlanDocument(**data)  # type: ignore[arg-type]
    errors = linter.validate_all(plan_doc, Path("test.yaml"))

    # then
    assert len(errors) > 0
    assert any("nonexistent" in e.message for e in errors)


async def test_lint_multiple_errors__when_multiple_issues__returns_all_errors() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "invalid",
                        "references": [],
                        "verification_spec": [],
                    }
                ],
                "execution": {"started": "true", "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
        "extra_field": "value",
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) >= 3
    assert any("work_plans[0].execution.started" in e.location for e in errors)
    assert any("work_plans[0].todos[0].status" in e.location for e in errors)
    assert any("extra_field" in e.location for e in errors)


async def test_lint_recursive_children__when_child_has_error__returns_error() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Parent",
                        "status": "pending",
                        "references": [],
                        "verification_spec": [],
                        "children": [
                            {
                                "id": "1.1",
                                "title": "Child",
                                "status": "invalid_status",
                                "references": [],
                                "verification_spec": [],
                            }
                        ],
                    }
                ],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert any("work_plans[0].todos[0].children[0].status" in e.location for e in errors)
    assert any("Invalid enum" in e.message for e in errors)


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


async def test_lint_verification_item_v2_1__when_bash_only__returns_no_errors() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "pending",
                        "references": [],
                        "verification_spec": [
                            {
                                "id": "v1",
                                "title": "check file",
                                "description": "check file exists",
                                "orchestrator_manually_verified": False,
                                "manual_verification_evidence": "",
                                "bash": [{"execute": "ls -al", "expected_exit_code": 0}],
                            }
                        ],
                    }
                ],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) == 0


async def test_lint_verification_item_v2_1__when_llm_judge_only__returns_no_errors() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "pending",
                        "references": [],
                        "verification_spec": [
                            {
                                "id": "v1",
                                "title": "llm check",
                                "description": "llm verification",
                                "orchestrator_manually_verified": False,
                                "manual_verification_evidence": "",
                                "llm_judge": [{"instruction": "check if correct"}],
                            }
                        ],
                    }
                ],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) == 0


async def test_lint_verification_item_v2_1__when_both_bash_and_llm__returns_no_errors() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "pending",
                        "references": [],
                        "verification_spec": [
                            {
                                "id": "v1",
                                "title": "both check",
                                "description": "both bash and llm",
                                "orchestrator_manually_verified": False,
                                "manual_verification_evidence": "",
                                "bash": [{"execute": "ls"}],
                                "llm_judge": [{"instruction": "verify"}],
                            }
                        ],
                    }
                ],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) == 0


async def test_lint_verification_item_v2_1__when_neither_bash_nor_llm__returns_error() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "pending",
                        "references": [],
                        "verification_spec": [
                            {
                                "id": "v1",
                                "title": "no verification",
                                "description": "missing both",
                                "orchestrator_manually_verified": False,
                                "manual_verification_evidence": "",
                            }
                        ],
                    }
                ],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) > 0
    assert any("bash or llm_judge is required" in e.message for e in errors)


async def test_lint_reference_pointer_v2_1__when_type_field_present__returns_no_errors() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {
                    "description": "Test",
                    "file_structure": None,
                    "references": [{"type": "file", "path": "a.py", "description": "File A", "id": "ref1"}],
                },
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "pending",
                        "references": [{"type": "pointer", "ref_id": "ref1"}],
                        "verification_spec": [],
                    }
                ],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) == 0


async def test_lint_final_verification_v2_1__when_category_field_present__returns_no_errors() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [
                    {
                        "id": "fv1",
                        "title": "Final check",
                        "category": "기능 동작 확인",
                        "description": "Verify all features work",
                        "orchestrator_manually_verified": False,
                        "manual_verification_evidence": "",
                        "bash": [{"execute": "pytest"}],
                    }
                ],
                "todos": [
                    {
                        "id": "1",
                        "title": "Task",
                        "status": "pending",
                        "references": [],
                        "verification_spec": [],
                    }
                ],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) == 0


async def test_validate_todos__if_empty__returns_error() -> None:
    # given
    linter = PlanLinter({})
    # v3.0 PlanDocument structure
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }

    # when
    errors = linter.lint(data)

    # then
    assert len(errors) == 1
    assert errors[0].location == "work_plans[0].todos"
    assert "empty" in errors[0].message.lower()
    assert errors[0].expected == "at least one todo"
    assert errors[0].actual == "empty list"


async def test_validate_all_success__when_all_checks_pass__returns_empty_list() -> None:
    # given
    linter = PlanLinter({})
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "plan-1",
                "name": "Valid Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test objective", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {
                        "id": "1",
                        "title": "Test task",
                        "status": "pending",
                        "references": [],
                        "verification_spec": [],
                    }
                ],
                "references": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }
    plan_doc = PlanDocument(**data)  # type: ignore[arg-type]
    plan_path = Path("/tmp/test.yaml")

    # when
    errors = linter.validate_all(plan_doc, plan_path)

    # then
    assert errors == []


async def test_validate_all_with_dependency_errors__when_missing_plan__returns_dependency_error() -> None:
    # given
    linter = PlanLinter({})
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "plan-1",
                "name": "Plan with missing dependency",
                "depends_on": ["nonexistent-plan"],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {"id": "1", "title": "Test", "status": "pending", "references": [], "verification_spec": []}
                ],
                "references": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }
    plan_doc = PlanDocument(**data)  # type: ignore[arg-type]
    plan_path = Path("/tmp/test.yaml")

    # when
    errors = linter.validate_all(plan_doc, plan_path)

    # then
    assert len(errors) > 0
    assert any(e.category == "dependency" for e in errors)
    assert any("nonexistent-plan" in e.message for e in errors)


async def test_validate_all_with_cycle_errors__when_circular_dependency__returns_cycle_error() -> None:
    # given
    linter = PlanLinter({})
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "plan-a",
                "name": "Plan A",
                "depends_on": ["plan-b"],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {"id": "1", "title": "Test", "status": "pending", "references": [], "verification_spec": []}
                ],
                "references": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            },
            {
                "id": "plan-b",
                "name": "Plan B",
                "depends_on": ["plan-a"],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {"id": "1", "title": "Test", "status": "pending", "references": [], "verification_spec": []}
                ],
                "references": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            },
        ],
    }
    plan_doc = PlanDocument(**data)  # type: ignore[arg-type]
    plan_path = Path("/tmp/test.yaml")

    # when
    errors = linter.validate_all(plan_doc, plan_path)

    # then
    assert len(errors) > 0
    assert any(e.category == "dependency" for e in errors)
    assert any("Circular dependency" in e.message for e in errors)


async def test_validate_all_returns_list_of_lint_errors__when_called__returns_correct_type() -> None:
    # given
    linter = PlanLinter({})
    data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-01-01", "updated_at": "2025-01-01"},
        "work_plans": [
            {
                "id": "plan-1",
                "name": "Test Plan",
                "depends_on": [],
                "user_request": {"original": "Test", "created_at": "2025-01-01", "additional": []},
                "objectives": {"core": "Test", "detailed": []},
                "background": {
                    "current_situation": "A",
                    "reason_for_change": "B",
                    "changes_to_make": "C",
                },
                "required_background": {"description": "Test", "file_structure": None, "references": []},
                "workflow": {"dependency_diagram": "Test", "critical_path": []},
                "success_vision": {"user_perspective": [], "business_perspective": [], "technical_criteria": []},
                "final_verification": [],
                "todos": [
                    {"id": "1", "title": "Test", "status": "pending", "references": [], "verification_spec": []}
                ],
                "references": [],
                "execution": {"started": False, "completed": False, "started_at": None, "completed_at": None},
                "work_mode": {"parallel_requested": False, "current_task_id": None},
                "current_work": "",
            }
        ],
    }
    plan_doc = PlanDocument(**data)  # type: ignore[arg-type]
    plan_path = Path("/tmp/test.yaml")

    # when
    errors = linter.validate_all(plan_doc, plan_path)

    # then
    assert isinstance(errors, list)
    assert all(isinstance(e, LintError) for e in errors)


async def test_lint_error_category_field__when_created__has_category() -> None:
    # given
    error = LintError(
        category="dependency",
        location="test",
        message="test message",
        expected="test expected",
        actual="test actual",
    )

    # then
    assert hasattr(error, "category")
    assert error.category == "dependency"
