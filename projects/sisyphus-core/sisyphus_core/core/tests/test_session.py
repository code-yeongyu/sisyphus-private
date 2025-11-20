from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import anyio
import pytest

from sisyphus_core.core.session import SessionStore

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = [pytest.mark.anyio]


@pytest.fixture()
async def temp_sessions_dir(tmp_path: Path) -> AsyncIterator[Path]:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    yield sessions_dir

    if sessions_dir.exists():
        for file in sessions_dir.iterdir():
            await anyio.to_thread.run_sync(file.unlink)
        await anyio.to_thread.run_sync(sessions_dir.rmdir)


@pytest.fixture()
async def session_store(temp_sessions_dir: Path) -> SessionStore:
    return SessionStore(base_dir=temp_sessions_dir)


async def test_session_store_initialization(temp_sessions_dir: Path) -> None:
    store = SessionStore(base_dir=temp_sessions_dir)

    assert store.base_dir == temp_sessions_dir
    assert store.sessions_file == temp_sessions_dir / "sessions.json"
    assert store.backup_file == temp_sessions_dir / "sessions.json.bak"
    assert temp_sessions_dir.exists()


async def test_save_and_load_session_with_plan_id(session_store: SessionStore) -> None:
    agent_type = "claude"
    session_id = "test-session-123"
    plan_id = "plan-foundation"

    await session_store.save_session(agent_type, session_id, plan_id)
    loaded_session = await session_store.get_session(agent_type, plan_id)

    assert loaded_session == session_id


async def test_get_nonexistent_session(session_store: SessionStore) -> None:
    agent_type = "nonexistent"
    plan_id = "plan-id"

    session = await session_store.get_session(agent_type, plan_id)

    assert session is None


async def test_plan_separation(session_store: SessionStore) -> None:
    agent_type = "claude"
    session_1 = "session-plan-1"
    session_2 = "session-plan-2"
    plan_1 = "plan-foundation"
    plan_2 = "plan-backend"

    await session_store.save_session(agent_type, session_1, plan_1)
    await session_store.save_session(agent_type, session_2, plan_2)

    assert await session_store.get_session(agent_type, plan_1) == session_1
    assert await session_store.get_session(agent_type, plan_2) == session_2


async def test_agent_and_plan_separation(session_store: SessionStore) -> None:
    claude_session = "claude-session-plan-a"
    opencode_session = "opencode-session-plan-a"
    plan_id = "plan-a"

    await session_store.save_session("claude", claude_session, plan_id)
    await session_store.save_session("opencode", opencode_session, plan_id)

    assert await session_store.get_session("claude", plan_id) == claude_session
    assert await session_store.get_session("opencode", plan_id) == opencode_session


async def test_session_update(session_store: SessionStore) -> None:
    agent_type = "claude"
    plan_id = "plan-foundation"
    old_session = "old-session"
    new_session = "new-session"

    await session_store.save_session(agent_type, old_session, plan_id)
    await session_store.save_session(agent_type, new_session, plan_id)
    loaded_session = await session_store.get_session(agent_type, plan_id)

    assert loaded_session == new_session


async def test_delete_specific_plan_session(session_store: SessionStore) -> None:
    agent_type = "claude"
    await session_store.save_session(agent_type, "session-1", "plan-1")
    await session_store.save_session(agent_type, "session-2", "plan-2")

    await session_store.delete_session(agent_type, "plan-1")

    assert await session_store.get_session(agent_type, "plan-1") is None
    assert await session_store.get_session(agent_type, "plan-2") == "session-2"


async def test_delete_all_plan_sessions(session_store: SessionStore) -> None:
    agent_type = "claude"
    await session_store.save_session(agent_type, "session-1", "plan-1")
    await session_store.save_session(agent_type, "session-2", "plan-2")

    await session_store.delete_session(agent_type)

    assert await session_store.get_session(agent_type, "plan-1") is None
    assert await session_store.get_session(agent_type, "plan-2") is None


async def test_delete_nonexistent_session(session_store: SessionStore) -> None:
    agent_type = "nonexistent"

    await session_store.delete_session(agent_type)


async def test_list_sessions(session_store: SessionStore) -> None:
    await session_store.save_session("claude", "session-1", "plan-1")
    await session_store.save_session("opencode", "session-2", "plan-2")

    sessions = await session_store.list_sessions()

    assert "claude" in sessions
    assert "opencode" in sessions
    assert "plan-1" in sessions["claude"]
    assert "plan-2" in sessions["opencode"]
    assert sessions["claude"]["plan-1"]["session_id"] == "session-1"
    assert sessions["opencode"]["plan-2"]["session_id"] == "session-2"


async def test_list_sessions_empty(session_store: SessionStore) -> None:
    sessions = await session_store.list_sessions()

    assert sessions == {}


async def test_atomic_write_creates_backup(session_store: SessionStore, temp_sessions_dir: Path) -> None:
    await session_store.save_session("claude", "first-session", "plan-1")
    backup_file = temp_sessions_dir / "sessions.json.bak"

    await session_store.save_session("opencode", "second-session", "plan-2")

    assert backup_file.exists()
    backup_content = await anyio.to_thread.run_sync(backup_file.read_text)
    backup_data: Any = json.loads(cast(str, backup_content))
    assert "claude" in backup_data


async def test_json_format_validity(session_store: SessionStore, temp_sessions_dir: Path) -> None:
    await session_store.save_session("claude", "test-session", "plan-foundation")
    sessions_file = temp_sessions_dir / "sessions.json"

    content_data = await anyio.to_thread.run_sync(sessions_file.read_text)
    content: str = cast(str, content_data)
    data: Any = json.loads(content)

    assert isinstance(data, dict)
    assert "claude" in data
    assert "plan-foundation" in data["claude"]
    assert "session_id" in data["claude"]["plan-foundation"]
    assert "updated" in data["claude"]["plan-foundation"]
    assert data["claude"]["plan-foundation"]["session_id"] == "test-session"


async def test_corruption_recovery_from_backup(session_store: SessionStore, temp_sessions_dir: Path) -> None:
    await session_store.save_session("claude", "backup-session", "plan-1")
    await session_store.save_session("opencode", "another-session", "plan-2")
    sessions_file = temp_sessions_dir / "sessions.json"

    await anyio.to_thread.run_sync(sessions_file.write_text, "invalid json{{{")

    loaded_session = await session_store.get_session("claude", "plan-1")

    assert loaded_session == "backup-session"


async def test_corruption_recovery_both_files_corrupted(session_store: SessionStore, temp_sessions_dir: Path) -> None:
    sessions_file = temp_sessions_dir / "sessions.json"
    backup_file = temp_sessions_dir / "sessions.json.bak"

    await anyio.to_thread.run_sync(sessions_file.write_text, "invalid json{{{")
    await anyio.to_thread.run_sync(backup_file.write_text, "also invalid}}}}")

    session = await session_store.get_session("claude", "plan-1")

    assert session is None


async def test_corruption_recovery_start_fresh(
    temp_sessions_dir: Path,
) -> None:
    sessions_file = temp_sessions_dir / "sessions.json"
    backup_file = temp_sessions_dir / "sessions.json.bak"

    await anyio.to_thread.run_sync(sessions_file.write_text, "corrupted{{{")
    await anyio.to_thread.run_sync(backup_file.write_text, "corrupted}}}")

    store = SessionStore(base_dir=temp_sessions_dir)

    await store.save_session("new_agent", "new-session", "plan-1")
    loaded_session = await store.get_session("new_agent", "plan-1")

    assert loaded_session == "new-session"


async def test_concurrent_access(session_store: SessionStore) -> None:
    num_operations = 10

    async def save_operation(index: int) -> None:
        await session_store.save_session(f"agent_{index}", f"session_{index}", f"plan_{index}")

    async with anyio.create_task_group() as tg:
        for i in range(num_operations):
            tg.start_soon(save_operation, i)

    sessions = await session_store.list_sessions()
    assert len(sessions) == num_operations  # type: ignore[arg-type]
    for i in range(num_operations):
        assert f"agent_{i}" in sessions
        assert f"plan_{i}" in sessions[f"agent_{i}"]
        assert sessions[f"agent_{i}"][f"plan_{i}"]["session_id"] == f"session_{i}"


async def test_concurrent_read_write(session_store: SessionStore) -> None:
    await session_store.save_session("shared", "initial", "plan-1")

    results: list[str | None] = []

    async def read_operation() -> None:
        session = await session_store.get_session("shared", "plan-1")
        results.append(session)

    async def write_operation(value: str) -> None:
        await session_store.save_session("shared", value, "plan-1")

    async with anyio.create_task_group() as tg:
        tg.start_soon(write_operation, "updated-1")
        tg.start_soon(read_operation)
        tg.start_soon(write_operation, "updated-2")
        tg.start_soon(read_operation)

    final_session = await session_store.get_session("shared", "plan-1")
    assert final_session in ["updated-1", "updated-2"]
    assert all(r in ["initial", "updated-1", "updated-2"] for r in results)


async def test_persistence_across_instances(temp_sessions_dir: Path) -> None:
    store1 = SessionStore(base_dir=temp_sessions_dir)
    await store1.save_session("persistent", "session-data", "plan-1")

    store2 = SessionStore(base_dir=temp_sessions_dir)
    loaded_session = await store2.get_session("persistent", "plan-1")

    assert loaded_session == "session-data"


async def test_file_not_exists_initially(temp_sessions_dir: Path) -> None:
    sessions_file = temp_sessions_dir / "sessions.json"
    assert not sessions_file.exists()

    store = SessionStore(base_dir=temp_sessions_dir)
    session = await store.get_session("any", "plan-1")

    assert session is None


async def test_unicode_session_ids(session_store: SessionStore) -> None:
    unicode_session = "세션-아이디-한글-🚀"

    await session_store.save_session("unicode_agent", unicode_session, "plan-한글")
    loaded_session = await session_store.get_session("unicode_agent", "plan-한글")

    assert loaded_session == unicode_session


async def test_get_nonexistent_plan_session(session_store: SessionStore) -> None:
    agent_type = "claude"
    plan_id = "nonexistent-plan"

    session = await session_store.get_session(agent_type, plan_id)

    assert session is None
