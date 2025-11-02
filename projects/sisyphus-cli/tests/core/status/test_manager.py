from pathlib import Path

import pytest

from sisyphus.core.status.manager import StatusFile, StatusManager

pytestmark = [pytest.mark.anyio]


async def test_status_manager__if_file_missing__get_returns_none_current_plan(tmp_path: Path) -> None:
    """status.json 파일이 없으면 current_plan=None 반환"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)

    # when
    result = await manager.get()

    # then
    assert isinstance(result, StatusFile)
    assert result.version == 1
    assert result.current_plan is None


async def test_status_manager__if_set_current__creates_file(tmp_path: Path) -> None:
    """set_current 호출 시 status.json 파일 생성"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)

    # when
    await manager.set_current(plan_path="plans/main.yaml", plan_root="plans/")

    # then
    assert status_path.exists()
    result = await manager.get()
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/main.yaml"
    assert result.current_plan.plan_root == "plans/"
    assert result.current_plan.updated_at


async def test_status_manager__if_set_current_twice__updates_file(tmp_path: Path) -> None:
    """set_current 두 번 호출 시 파일 업데이트"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)
    await manager.set_current("plans/old.yaml", "plans/")

    # when
    await manager.set_current("plans/new.yaml", "plans/")

    # then
    result = await manager.get()
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/new.yaml"


async def test_status_manager__if_file_exists__get_reads_correctly(tmp_path: Path) -> None:
    """기존 status.json 파일 정상 읽기"""
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)
    await manager.set_current("plans/test.yaml", "plans/")

    # when
    result = await manager.get()

    # then
    assert result.version == 1
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/test.yaml"
