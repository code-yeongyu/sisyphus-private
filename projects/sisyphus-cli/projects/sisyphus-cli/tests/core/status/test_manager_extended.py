"""Tests for extended StatusManager functionality (v3.0 support)."""

import json
from pathlib import Path

import pytest

from sisyphus.core.status.manager import CurrentPlan, StatusFile, StatusManager


@pytest.fixture
async def status_manager(tmp_path: Path) -> StatusManager:
    """Create a StatusManager with a temporary status file."""
    status_path = tmp_path / ".sisyphus" / "status.json"
    return StatusManager(status_path)


@pytest.mark.anyio
async def test_set_current_with_plan_id(status_manager: StatusManager) -> None:
    """Test setting current plan with plan_id."""
    # given
    plan_path = ".sisyphus/tasks/test.yaml"
    plan_root = "/test/root"
    plan_id = "test-plan"
    
    # when
    await status_manager.set_current(
        plan_path=plan_path,
        plan_root=plan_root,
        plan_id=plan_id,
    )
    
    # then
    status = await status_manager.get()
    assert status is not None
    assert status.current_plan is not None
    assert status.current_plan.plan_id == plan_id
    assert status.current_plan.plan_path == plan_path
    assert status.current_plan.plan_root == plan_root


@pytest.mark.anyio
async def test_set_current_with_current_task_id(status_manager: StatusManager) -> None:
    """Test setting current plan with current_task_id."""
    # given
    plan_path = ".sisyphus/tasks/test.yaml"
    plan_root = "/test/root"
    plan_id = "test-plan"
    current_task_id = "task-1"
    
    # when
    await status_manager.set_current(
        plan_path=plan_path,
        plan_root=plan_root,
        plan_id=plan_id,
        current_task_id=current_task_id,
    )
    
    # then
    status = await status_manager.get()
    assert status is not None
    assert status.current_plan is not None
    assert status.current_plan.current_task_id == current_task_id


@pytest.mark.anyio
async def test_set_current_with_none_task_id(status_manager: StatusManager) -> None:
    """Test setting current plan with None current_task_id."""
    # given
    plan_path = ".sisyphus/tasks/test.yaml"
    plan_root = "/test/root"
    plan_id = "test-plan"
    
    # when
    await status_manager.set_current(
        plan_path=plan_path,
        plan_root=plan_root,
        plan_id=plan_id,
        current_task_id=None,
    )
    
    # then
    status = await status_manager.get()
    assert status is not None
    assert status.current_plan is not None
    assert status.current_plan.current_task_id is None


@pytest.mark.anyio
async def test_update_current_task_id(status_manager: StatusManager) -> None:
    """Test updating current_task_id."""
    # given
    plan_path = ".sisyphus/tasks/test.yaml"
    plan_root = "/test/root"
    plan_id = "test-plan"
    
    await status_manager.set_current(
        plan_path=plan_path,
        plan_root=plan_root,
        plan_id=plan_id,
        current_task_id="task-1",
    )
    
    # when: Update to task-2
    await status_manager.set_current(
        plan_path=plan_path,
        plan_root=plan_root,
        plan_id=plan_id,
        current_task_id="task-2",
    )
    
    # then
    status = await status_manager.get()
    assert status is not None
    assert status.current_plan is not None
    assert status.current_plan.current_task_id == "task-2"


@pytest.mark.anyio
async def test_status_file_json_format(status_manager: StatusManager) -> None:
    """Test that status.json contains new fields in correct format."""
    # given
    plan_path = ".sisyphus/tasks/test.yaml"
    plan_root = "/test/root"
    plan_id = "test-plan"
    current_task_id = "task-1"
    
    # when
    await status_manager.set_current(
        plan_path=plan_path,
        plan_root=plan_root,
        plan_id=plan_id,
        current_task_id=current_task_id,
    )
    
    # then: Read raw JSON
    with open(status_manager.status_path) as f:
        data = json.load(f)
    
    assert data["version"] == 1
    assert data["current_plan"]["plan_id"] == plan_id
    assert data["current_plan"]["current_task_id"] == current_task_id
    assert data["current_plan"]["plan_path"] == plan_path
    assert data["current_plan"]["plan_root"] == plan_root
    assert "updated_at" in data["current_plan"]
