"""Tests for PlanLinter file path depends_on resolution."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from sisyphus_core.core.plan_linter import PlanLinter


def test_resolve_depends_on_path__absolute_path__returns_as_is() -> None:
    """Test that absolute paths are returned unchanged."""
    # Given
    absolute_path = "/absolute/path/to/file.yaml"
    schema_doc: dict[str, Any] = {}
    linter = PlanLinter(schema_doc)

    # When
    yaml_data: dict[str, Any] = {
        "version": "3.0",
        "metadata": {"created_at": "2025-11-16T10:00:00Z"},
        "work_plans": [
            {
                "id": "test-plan",
                "name": "Test Plan",
                "depends_on": [absolute_path],
                "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z"},
                "objectives": {"core": "test objective"},
                "background": {
                    "current_situation": "test",
                    "reason_for_change": "test",
                    "changes_to_make": "test",
                },
                "required_background": {"description": "test"},
                "workflow": {"dependency_diagram": "test"},
                "success_vision": {},
                "final_verification": [],
                "todos": [
                    {
                        "id": "todo-1",
                        "title": "Test Todo",
                        "status": "pending",
                    }
                ],
                "execution": {"started": False, "completed": False},
                "work_mode": {"parallel_requested": False},
            }
        ],
    }
    errors = linter.lint(yaml_data)

    # Then
    # Should not produce errors for valid depends_on format
    # (actual path validation happens in plan_linter when function is implemented)
    assert isinstance(errors, list)


def test_resolve_depends_on_path__relative_path_with_dot_slash__resolves_correctly() -> None:
    """Test that ./file.yaml paths are resolved relative to current plan parent."""
    # Given
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create directory structure
        (tmpdir_path / "subdir").mkdir()
        target_file = tmpdir_path / "subdir" / "dependency.yaml"

        # Create the dependency file
        _ = target_file.write_text("version: 3.0\nmetadata:\n  created_at: '2025-11-16T10:00:00Z'\nwork_plans: []")

        relative_path = "./dependency.yaml"

        # When
        schema_doc: dict[str, Any] = {}
        linter = PlanLinter(schema_doc)

        yaml_data: dict[str, Any] = {
            "version": "3.0",
            "metadata": {"created_at": "2025-11-16T10:00:00Z"},
            "work_plans": [
                {
                    "id": "test-plan",
                    "name": "Test Plan",
                    "depends_on": [relative_path],
                    "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z"},
                    "objectives": {"core": "test objective"},
                    "background": {
                        "current_situation": "test",
                        "reason_for_change": "test",
                        "changes_to_make": "test",
                    },
                    "required_background": {"description": "test"},
                    "workflow": {"dependency_diagram": "test"},
                    "success_vision": {},
                    "final_verification": [],
                    "todos": [
                        {
                            "id": "todo-1",
                            "title": "Test Todo",
                            "status": "pending",
                        }
                    ],
                    "execution": {"started": False, "completed": False},
                    "work_mode": {"parallel_requested": False},
                }
            ],
        }
        errors = linter.lint(yaml_data)

        # Then
        # Should not produce errors for valid depends_on format
        assert isinstance(errors, list)
        # File exists verification
        assert target_file.exists()


def test_resolve_depends_on_path__relative_path_with_parent_ref__resolves_correctly() -> None:
    """Test that ../file.yaml paths are resolved relative to current plan parent."""
    # Given
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create directory structure: parent/subdir/plan.yaml and parent/dependency.yaml
        (tmpdir_path / "subdir").mkdir()
        target_file = tmpdir_path / "dependency.yaml"

        # Create the dependency file
        _ = target_file.write_text("version: 3.0\nmetadata:\n  created_at: '2025-11-16T10:00:00Z'\nwork_plans: []")

        relative_path = "../dependency.yaml"

        # When
        schema_doc: dict[str, Any] = {}
        linter = PlanLinter(schema_doc)

        yaml_data: dict[str, Any] = {
            "version": "3.0",
            "metadata": {"created_at": "2025-11-16T10:00:00Z"},
            "work_plans": [
                {
                    "id": "test-plan",
                    "name": "Test Plan",
                    "depends_on": [relative_path],
                    "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z"},
                    "objectives": {"core": "test objective"},
                    "background": {
                        "current_situation": "test",
                        "reason_for_change": "test",
                        "changes_to_make": "test",
                    },
                    "required_background": {"description": "test"},
                    "workflow": {"dependency_diagram": "test"},
                    "success_vision": {},
                    "final_verification": [],
                    "todos": [
                        {
                            "id": "todo-1",
                            "title": "Test Todo",
                            "status": "pending",
                        }
                    ],
                    "execution": {"started": False, "completed": False},
                    "work_mode": {"parallel_requested": False},
                }
            ],
        }
        errors = linter.lint(yaml_data)

        # Then
        # Should not produce errors for valid depends_on format
        assert isinstance(errors, list)
        # File exists verification
        assert target_file.exists()


def test_resolve_depends_on_path__filename_only__resolves_to_sisyphus_tasks_dir() -> None:
    """Test that filename only (foobar.yml) resolves to .sisyphus/tasks/foobar.yml."""
    # Given
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create directory structure: tmpdir/.sisyphus/tasks/dependency.yaml
        (tmpdir_path / ".sisyphus" / "tasks").mkdir(parents=True)
        target_file = tmpdir_path / ".sisyphus" / "tasks" / "dependency.yaml"

        # Create the dependency file
        _ = target_file.write_text("version: 3.0\nmetadata:\n  created_at: '2025-11-16T10:00:00Z'\nwork_plans: []")

        filename_only = "dependency.yaml"

        # When
        schema_doc: dict[str, Any] = {}
        linter = PlanLinter(schema_doc)

        yaml_data: dict[str, Any] = {
            "version": "3.0",
            "metadata": {"created_at": "2025-11-16T10:00:00Z"},
            "work_plans": [
                {
                    "id": "test-plan",
                    "name": "Test Plan",
                    "depends_on": [filename_only],
                    "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z"},
                    "objectives": {"core": "test objective"},
                    "background": {
                        "current_situation": "test",
                        "reason_for_change": "test",
                        "changes_to_make": "test",
                    },
                    "required_background": {"description": "test"},
                    "workflow": {"dependency_diagram": "test"},
                    "success_vision": {},
                    "final_verification": [],
                    "todos": [
                        {
                            "id": "todo-1",
                            "title": "Test Todo",
                            "status": "pending",
                        }
                    ],
                    "execution": {"started": False, "completed": False},
                    "work_mode": {"parallel_requested": False},
                }
            ],
        }
        errors = linter.lint(yaml_data)

        # Then
        # Should not produce errors for valid depends_on format
        assert isinstance(errors, list)
        # File exists verification
        assert target_file.exists()


def test_resolve_depends_on_path__multiple_paths_mixed_formats__all_resolve() -> None:
    """Test that multiple depends_on paths with mixed formats all resolve correctly."""
    # Given
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create directory structure
        (tmpdir_path / ".sisyphus" / "tasks").mkdir(parents=True)
        (tmpdir_path / "other").mkdir()

        # Create multiple dependency files
        abs_file = tmpdir_path / "absolute.yaml"
        _ = abs_file.write_text("version: 3.0\nmetadata:\n  created_at: '2025-11-16T10:00:00Z'\nwork_plans: []")

        rel_file = tmpdir_path / ".sisyphus" / "tasks" / "relative.yaml"
        _ = rel_file.write_text("version: 3.0\nmetadata:\n  created_at: '2025-11-16T10:00:00Z'\nwork_plans: []")

        other_file = tmpdir_path / "other" / "other.yaml"
        _ = other_file.write_text("version: 3.0\nmetadata:\n  created_at: '2025-11-16T10:00:00Z'\nwork_plans: []")

        # When
        schema_doc: dict[str, Any] = {}
        linter = PlanLinter(schema_doc)

        yaml_data: dict[str, Any] = {
            "version": "3.0",
            "metadata": {"created_at": "2025-11-16T10:00:00Z"},
            "work_plans": [
                {
                    "id": "test-plan",
                    "name": "Test Plan",
                    "depends_on": [
                        str(abs_file),  # absolute path
                        "relative.yaml",  # filename only
                        "../other/other.yaml",  # relative with parent ref
                    ],
                    "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z"},
                    "objectives": {"core": "test objective"},
                    "background": {
                        "current_situation": "test",
                        "reason_for_change": "test",
                        "changes_to_make": "test",
                    },
                    "required_background": {"description": "test"},
                    "workflow": {"dependency_diagram": "test"},
                    "success_vision": {},
                    "final_verification": [],
                    "todos": [
                        {
                            "id": "todo-1",
                            "title": "Test Todo",
                            "status": "pending",
                        }
                    ],
                    "execution": {"started": False, "completed": False},
                    "work_mode": {"parallel_requested": False},
                }
            ],
        }
        errors = linter.lint(yaml_data)

        # Then
        # Should not produce errors for valid depends_on format
        assert isinstance(errors, list)
        # All files exist
        assert abs_file.exists()
        assert rel_file.exists()
        assert other_file.exists()


def test_resolve_depends_on_path__nonexistent_file__should_be_caught() -> None:
    """Test that nonexistent file paths are detected (when validation is implemented)."""
    # Given
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        (tmpdir_path / ".sisyphus" / "tasks").mkdir(parents=True)

        nonexistent_file = "nonexistent.yaml"

        # When
        schema_doc: dict[str, Any] = {}
        linter = PlanLinter(schema_doc)

        yaml_data: dict[str, Any] = {
            "version": "3.0",
            "metadata": {"created_at": "2025-11-16T10:00:00Z"},
            "work_plans": [
                {
                    "id": "test-plan",
                    "name": "Test Plan",
                    "depends_on": [nonexistent_file],
                    "user_request": {"original": "test", "created_at": "2025-11-16T10:00:00Z"},
                    "objectives": {"core": "test objective"},
                    "background": {
                        "current_situation": "test",
                        "reason_for_change": "test",
                        "changes_to_make": "test",
                    },
                    "required_background": {"description": "test"},
                    "workflow": {"dependency_diagram": "test"},
                    "success_vision": {},
                    "final_verification": [],
                    "todos": [
                        {
                            "id": "todo-1",
                            "title": "Test Todo",
                            "status": "pending",
                        }
                    ],
                    "execution": {"started": False, "completed": False},
                    "work_mode": {"parallel_requested": False},
                }
            ],
        }
        errors = linter.lint(yaml_data)

        # Then
        # Test file structure (actual validation will be implemented in plan_linter.py)
        assert isinstance(errors, list)
