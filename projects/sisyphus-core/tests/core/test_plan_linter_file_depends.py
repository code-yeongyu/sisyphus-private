"""Test depends_on file path resolution for different path formats."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from sisyphus_core.core.plan_linter import PlanLinter
from sisyphus_core.core.plans.models import PlanDocument


@pytest.mark.anyio
async def test_resolve_depends_on_path__if_absolute_path__then_return_as_is() -> None:
    """Given: depends_on with absolute path (/absolute/path/to/file.yml).
    When: resolve_depends_on_path is called.
    Then: Return the absolute path as-is.
    """
    # Given
    depends_on = "/absolute/path/to/file.yml"
    current_plan_path = Path("/project/.sisyphus/tasks/plan.yaml")
    schema_doc = PlanDocument(version="3.0", metadata={"created_at": "2025-11-16T10:00:00Z"}, work_plans=[])
    linter = PlanLinter(schema_doc)

    # When
    result = linter.resolve_depends_on_path(depends_on, current_plan_path)

    # Then
    assert result == Path("/absolute/path/to/file.yml")


@pytest.mark.anyio
async def test_resolve_depends_on_path__if_relative_with_dot_slash__then_resolve_from_parent() -> None:
    """Given: depends_on with relative path (./subdir/file.yml).
    When: resolve_depends_on_path is called.
    Then: Resolve relative to current plan file's parent directory.
    """
    # Given
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_dir = tmppath / "project"
        tasks_dir = project_dir / ".sisyphus" / "tasks"
        tasks_dir.mkdir(parents=True)

        current_plan_path = tasks_dir / "plan.yaml"
        depends_on = "./other_file.yml"
        schema_doc = PlanDocument(version="3.0", metadata={"created_at": "2025-11-16T10:00:00Z"}, work_plans=[])
        linter = PlanLinter(schema_doc)

        # When
        result = linter.resolve_depends_on_path(depends_on, current_plan_path)

        # Then
        expected = (tasks_dir / "other_file.yml").resolve()
        assert result == expected


@pytest.mark.anyio
async def test_resolve_depends_on_path__if_relative_with_double_dot__then_resolve_from_parent() -> None:
    """Given: depends_on with relative path (../other_dir/file.yml).
    When: resolve_depends_on_path is called.
    Then: Resolve relative to current plan file's parent directory.
    """
    # Given
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_dir = tmppath / "project"
        tasks_dir = project_dir / ".sisyphus" / "tasks"
        other_dir = project_dir / ".sisyphus" / "other"
        other_dir.mkdir(parents=True)

        current_plan_path = tasks_dir / "plan.yaml"
        depends_on = "../other/file.yml"
        schema_doc = PlanDocument(version="3.0", metadata={"created_at": "2025-11-16T10:00:00Z"}, work_plans=[])
        linter = PlanLinter(schema_doc)

        # When
        result = linter.resolve_depends_on_path(depends_on, current_plan_path)

        # Then
        expected = (other_dir / "file.yml").resolve()
        assert result == expected


@pytest.mark.anyio
async def test_resolve_depends_on_path__if_plan_in_tasks_dir_and_filename_only__then_no_duplicate() -> None:
    """Given: Plan file already in .sisyphus/tasks/ directory, depends_on is filename only.
    When: resolve_depends_on_path is called.
    Then: Return path WITHOUT duplicate .sisyphus/tasks/ directory.
    """
    # Given
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_dir = tmppath / "project"
        tasks_dir = project_dir / ".sisyphus" / "tasks"
        tasks_dir.mkdir(parents=True)

        current_plan_path = tasks_dir / "plan.yaml"
        depends_on = "foobar.yml"
        schema_doc = PlanDocument(version="3.0", metadata={"created_at": "2025-11-16T10:00:00Z"}, work_plans=[])
        linter = PlanLinter(schema_doc)

        # When
        result = linter.resolve_depends_on_path(depends_on, current_plan_path)

        # Then - should be /project/.sisyphus/tasks/foobar.yml, NOT /project/.sisyphus/tasks/.sisyphus/tasks/foobar.yml
        expected = (tasks_dir / "foobar.yml").resolve()
        assert result == expected
        assert str(result).count(".sisyphus/tasks") == 1, f"Duplicate .sisyphus/tasks found in {result}"


@pytest.mark.anyio
async def test_resolve_depends_on_path__if_plan_not_in_tasks_dir_and_filename_only__then_add_tasks_path() -> None:
    """Given: Plan file NOT in .sisyphus/tasks/ directory, depends_on is filename only.
    When: resolve_depends_on_path is called.
    Then: Add .sisyphus/tasks/ to the path.
    """
    # Given
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_dir = tmppath / "project"
        other_dir = project_dir / "other"
        other_dir.mkdir(parents=True)
        tasks_dir = project_dir / ".sisyphus" / "tasks"
        tasks_dir.mkdir(parents=True)

        current_plan_path = other_dir / "plan.yaml"
        depends_on = "foobar.yml"
        schema_doc = PlanDocument(version="3.0", metadata={"created_at": "2025-11-16T10:00:00Z"}, work_plans=[])
        linter = PlanLinter(schema_doc)

        # When
        result = linter.resolve_depends_on_path(depends_on, current_plan_path)

        # Then - should add .sisyphus/tasks to other_dir path
        expected = (other_dir / ".sisyphus" / "tasks" / "foobar.yml").resolve()
        assert result == expected


@pytest.mark.anyio
async def test_resolve_depends_on_path__if_deeply_nested_tasks_dir__then_still_check_correct_parent() -> None:
    """Given: Plan file in deeply nested tasks directory (e.g., /a/b/.sisyphus/tasks/).
    When: resolve_depends_on_path is called with filename only.
    Then: Should detect parent correctly and not duplicate path.
    """
    # Given
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_dir = tmppath / "a" / "b"
        tasks_dir = project_dir / ".sisyphus" / "tasks"
        tasks_dir.mkdir(parents=True)

        current_plan_path = tasks_dir / "plan.yaml"
        depends_on = "foobar.yml"
        schema_doc = PlanDocument(version="3.0", metadata={"created_at": "2025-11-16T10:00:00Z"}, work_plans=[])
        linter = PlanLinter(schema_doc)

        # When
        result = linter.resolve_depends_on_path(depends_on, current_plan_path)

        # Then - should NOT have duplicate .sisyphus/tasks
        expected = (tasks_dir / "foobar.yml").resolve()
        assert result == expected
        assert str(result).count(".sisyphus/tasks") == 1
