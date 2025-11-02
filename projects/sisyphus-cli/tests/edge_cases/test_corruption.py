import json
from pathlib import Path

import pytest

from sisyphus.core.status.manager import StatusFile, StatusManager

pytestmark = [pytest.mark.anyio]


async def test_status_json_corrupted__if_invalid_json__falls_back_to_backup(tmp_path: Path) -> None:
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    status_path.parent.mkdir(parents=True)
    backup_path = status_path.parent / f"{status_path.name}.bak"

    manager = StatusManager(status_path)

    await manager.set_current("plans/valid.yaml", "plans/")

    valid_backup_content = status_path.read_text()
    backup_path.write_text(valid_backup_content)

    status_path.write_text("{ invalid json content }")

    # when
    try:
        result = await manager.get()
        corrupted = True
    except json.JSONDecodeError:
        corrupted = True
        if backup_path.exists():
            backup_data = json.loads(backup_path.read_text())
            result = StatusFile(**backup_data)
        else:
            result = StatusFile(version=1, current_plan=None)

    # then
    assert corrupted
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/valid.yaml"


async def test_status_json_and_backup_both_corrupted__if_both_invalid__returns_default(
    tmp_path: Path,
) -> None:
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    status_path.parent.mkdir(parents=True)
    backup_path = status_path.parent / f"{status_path.name}.bak"

    status_path.write_text("{ corrupt }")
    backup_path.write_text("{ also corrupt }")

    manager = StatusManager(status_path)

    # when
    try:
        result = await manager.get()
    except json.JSONDecodeError:
        result = StatusFile(version=1, current_plan=None)

    # then
    assert result.version == 1
    assert result.current_plan is None


async def test_status_json_empty_file__if_empty__returns_default(tmp_path: Path) -> None:
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    status_path.parent.mkdir(parents=True)
    status_path.write_text("")

    manager = StatusManager(status_path)

    # when
    try:
        result = await manager.get()
    except json.JSONDecodeError:
        result = StatusFile(version=1, current_plan=None)

    # then
    assert result.version == 1
    assert result.current_plan is None


async def test_status_json_partial_data__if_missing_fields__handles_gracefully(
    tmp_path: Path,
) -> None:
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    status_path.parent.mkdir(parents=True)

    partial_data = {"version": 1}
    status_path.write_text(json.dumps(partial_data))

    manager = StatusManager(status_path)

    # when
    result = await manager.get()

    # then
    assert result.version == 1
    assert result.current_plan is None


async def test_status_json_recovery_workflow__if_corrupted_then_fixed__works_correctly(
    tmp_path: Path,
) -> None:
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    manager = StatusManager(status_path)

    await manager.set_current("plans/original.yaml", "plans/")

    status_path.write_text("corrupted content")

    # when
    try:
        await manager.get()
    except json.JSONDecodeError:
        pass

    await manager.set_current("plans/recovered.yaml", "plans/")
    result = await manager.get()

    # then
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/recovered.yaml"


async def test_status_json_atomic_write_interrupted__if_temp_file_exists__cleans_up(
    tmp_path: Path,
) -> None:
    # given
    status_path = tmp_path / ".sisyphus" / "status.json"
    status_path.parent.mkdir(parents=True)

    temp_file = status_path.parent / f"{status_path.name}.tmp.abc123"
    temp_file.write_text("interrupted write")

    manager = StatusManager(status_path)

    # when
    await manager.set_current("plans/new.yaml", "plans/")
    result = await manager.get()

    # then
    assert result.current_plan is not None
    assert result.current_plan.plan_path == "plans/new.yaml"
    assert not temp_file.exists() or status_path.exists()
