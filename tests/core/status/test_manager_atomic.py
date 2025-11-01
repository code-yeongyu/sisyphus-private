from pathlib import Path

import anyio
import pytest

from sisyphus.core.status.manager import StatusManager

pytestmark = [pytest.mark.anyio]


async def test_status_manager__if_atomic_write__creates_temp_file_then_renames(tmp_path: Path) -> None:
    """원자적 쓰기 시 임시파일 생성 후 rename"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)

    # when
    await manager.set_current(plan_path="plans/test.yaml", plan_root="plans/")

    # then
    assert status_path.exists()
    result = await manager.get()
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/test.yaml"


async def test_status_manager__if_write_twice__creates_backup(tmp_path: Path) -> None:
    """두 번째 쓰기 시 백업 파일 생성"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    backup_path = tmp_path / ".sisyphus" / "status.json.bak"
    manager = StatusManager(status_path)
    await manager.set_current("plans/old.yaml", "plans/")

    # when
    await manager.set_current("plans/new.yaml", "plans/")

    # then
    assert status_path.exists()
    assert backup_path.exists()
    result = await manager.get()
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/new.yaml"


async def test_status_manager__if_concurrent_writes__no_race_condition(tmp_path: Path) -> None:
    """동시 쓰기 시 race condition 없음"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)

    async def write_plan(plan_id: str) -> None:
        await manager.set_current(f"plans/{plan_id}.yaml", "plans/")

    # when
    async with anyio.create_task_group() as tg:
        for i in range(10):
            tg.start_soon(write_plan, f"plan-{i}")

    # then
    assert status_path.exists()
    result = await manager.get()
    assert result.current_plan is not None
    assert result.current_plan.plan_path.startswith("plans/plan-")


async def test_status_manager__if_write_succeeds__no_temp_files_left(tmp_path: Path) -> None:
    """쓰기 성공 시 임시파일 남지 않음"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)

    # when
    await manager.set_current("plans/test.yaml", "plans/")

    # then
    temp_files = list(status_path.parent.glob("*.tmp.*"))
    assert len(temp_files) == 0
    assert status_path.exists()


async def test_status_manager__if_lock_held__waits_for_release(tmp_path: Path) -> None:
    """Lock이 잡혀있으면 대기"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)
    write_order = []

    async def slow_write(plan_id: str) -> None:
        await manager.set_current(f"plans/{plan_id}.yaml", "plans/")
        write_order.append(plan_id)
        await anyio.sleep(0.01)

    # when
    async with anyio.create_task_group() as tg:
        tg.start_soon(slow_write, "first")
        await anyio.sleep(0.001)
        tg.start_soon(slow_write, "second")

    # then
    assert len(write_order) == 2
    assert "first" in write_order
    assert "second" in write_order


async def test_status_manager__if_backup_exists__replaces_backup(tmp_path: Path) -> None:
    """기존 백업이 있으면 교체"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    backup_path = tmp_path / ".sisyphus" / "status.json.bak"
    manager = StatusManager(status_path)
    await manager.set_current("plans/first.yaml", "plans/")
    await manager.set_current("plans/second.yaml", "plans/")

    # when
    await manager.set_current("plans/third.yaml", "plans/")

    # then
    assert backup_path.exists()
    result = await manager.get()
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/third.yaml"
