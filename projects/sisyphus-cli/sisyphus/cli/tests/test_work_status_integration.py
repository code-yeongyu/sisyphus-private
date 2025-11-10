"""Integration tests for work and task continue synchronization via status.json."""

from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus.core.status.manager import StatusManager

pytestmark = [pytest.mark.anyio]


async def test_work_and_task_continue__use_same_plan_via_status_json(
    tmp_path: Path,
) -> None:
    """Verify work and task continue synchronize via status.json.

    This test simulates the workflow:
    1. User runs 'sisyphus task continue' → selects plan-A → status.json records it
    2. User runs 'sisyphus work' → automatically uses plan-A from status.json
    3. No need to select plan twice

    The test verifies StatusManager API (get/set_current) correctly
    reads and writes status.json.
    """
    # given: Setup .sisyphus/tasks/ with a test YAML file
    sisyphus_dir = tmp_path / ".sisyphus"
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir(parents=True)

    test_plan = tasks_dir / "test-plan.yaml"
    test_plan.write_text("""version: '3.0'
metadata:
  created_at: '2025-11-10T00:00:00Z'
  updated_at: '2025-11-10T00:00:00Z'
work_plans:
- id: test-plan-id
  name: Test Plan
  depends_on: []
  todos: []
""")

    # Create StatusManager with test path
    status_path = sisyphus_dir / "status.json"
    status_manager = StatusManager(status_path)

    # when: Simulate task continue writing to status.json
    await status_manager.set_current(
        plan_path=str(test_plan),
        plan_root=str(tmp_path),
    )

    # then: Verify status.json contains the plan
    status_file = await status_manager.get()
    assert status_file.current_plan is not None
    assert status_file.current_plan.plan_path == str(test_plan)

    # when: Simulate work reading from status.json
    # (This verifies _detect_plan_path() will find the plan)
    status_file_again = await status_manager.get()

    # then: Same plan is returned
    assert status_file_again.current_plan is not None
    assert status_file_again.current_plan.plan_path == str(test_plan)
    assert status_file_again.current_plan.plan_root == str(tmp_path)


async def test_status_manager__no_status_json__returns_empty(
    tmp_path: Path,
) -> None:
    """Verify StatusManager returns empty StatusFile when status.json doesn't exist."""
    # given: Empty directory (no status.json)
    status_path = tmp_path / ".sisyphus" / "status.json"
    status_manager = StatusManager(status_path)

    # when: Get status
    status_file = await status_manager.get()

    # then: Returns empty StatusFile with version=1 and no current_plan
    assert status_file.version == 1
    assert status_file.current_plan is None


async def test_status_manager__set_current__creates_status_json(
    tmp_path: Path,
) -> None:
    """Verify StatusManager creates status.json with correct structure."""
    # given: Empty directory
    status_path = tmp_path / ".sisyphus" / "status.json"
    status_manager = StatusManager(status_path)

    test_plan_path = "/path/to/plan.yaml"
    test_plan_root = "/path/to/root"

    # when: Set current plan
    await status_manager.set_current(
        plan_path=test_plan_path,
        plan_root=test_plan_root,
    )

    # then: status.json file created
    assert status_path.exists()

    # and: Contains correct data
    status_file = await status_manager.get()
    assert status_file.current_plan is not None
    assert status_file.current_plan.plan_path == test_plan_path
    assert status_file.current_plan.plan_root == test_plan_root
    assert status_file.current_plan.updated_at is not None  # Timestamp exists


async def test_status_manager__multiple_updates__preserves_latest(
    tmp_path: Path,
) -> None:
    """Verify StatusManager updates status.json correctly on multiple calls."""
    # given: StatusManager with initial plan
    status_path = tmp_path / ".sisyphus" / "status.json"
    status_manager = StatusManager(status_path)

    await status_manager.set_current(
        plan_path="/path/to/plan-A.yaml",
        plan_root="/root-A",
    )

    # when: Update to different plan
    await status_manager.set_current(
        plan_path="/path/to/plan-B.yaml",
        plan_root="/root-B",
    )

    # then: Latest plan is returned
    status_file = await status_manager.get()
    assert status_file.current_plan is not None
    assert status_file.current_plan.plan_path == "/path/to/plan-B.yaml"
    assert status_file.current_plan.plan_root == "/root-B"
