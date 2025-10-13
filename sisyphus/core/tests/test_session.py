from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import pytest

from sisyphus.core.session import SessionStore

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = [pytest.mark.anyio]


@pytest.fixture()
async def temp_sessions_dir(tmp_path: Path) -> AsyncIterator[Path]:
    # given
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    yield sessions_dir

    # cleanup
    if sessions_dir.exists():
        for file in sessions_dir.iterdir():
            await anyio.to_thread.run_sync(file.unlink)
        await anyio.to_thread.run_sync(sessions_dir.rmdir)


@pytest.fixture()
async def session_store(temp_sessions_dir: Path) -> SessionStore:
    # given
    return SessionStore(base_dir=temp_sessions_dir)


async def test_session_store_initialization(temp_sessions_dir: Path) -> None:
    # given
    store = SessionStore(base_dir=temp_sessions_dir)

    # when
    # (initialization happens in constructor)

    # then
    assert store.base_dir == temp_sessions_dir
    assert store.sessions_file == temp_sessions_dir / "sessions.json"
    assert store.backup_file == temp_sessions_dir / "sessions.json.bak"
    assert temp_sessions_dir.exists()


async def test_save_and_load_session(session_store: SessionStore) -> None:
    # given
    agent_type = "claude"
    session_id = "test-session-123"

    # when
    await session_store.save_session(agent_type, session_id)
    loaded_session = await session_store.get_session(agent_type)

    # then
    assert loaded_session == session_id


async def test_get_nonexistent_session(session_store: SessionStore) -> None:
    # given
    agent_type = "nonexistent"

    # when
    session = await session_store.get_session(agent_type)

    # then
    assert session is None


async def test_agent_separation(session_store: SessionStore) -> None:
    # given
    claude_session = "claude-session-456"
    opencode_session_1 = "opencode-session-789"

    # when
    await session_store.save_session("claude", claude_session)
    await session_store.save_session("opencode", opencode_session_1)

    # then
    assert await session_store.get_session("claude") == claude_session
    assert await session_store.get_session("opencode") == opencode_session_1


async def test_session_update(session_store: SessionStore) -> None:
    # given
    agent_type = "claude"
    old_session = "old-session"
    new_session = "new-session"

    # when
    await session_store.save_session(agent_type, old_session)
    await session_store.save_session(agent_type, new_session)
    loaded_session = await session_store.get_session(agent_type)

    # then
    assert loaded_session == new_session


async def test_delete_session(session_store: SessionStore) -> None:
    # given
    agent_type = "opencode"
    session_id = "session-to-delete"
    await session_store.save_session(agent_type, session_id)

    # when
    await session_store.delete_session(agent_type)
    loaded_session = await session_store.get_session(agent_type)

    # then
    assert loaded_session is None


async def test_delete_nonexistent_session(session_store: SessionStore) -> None:
    # given
    agent_type = "nonexistent"

    # when
    await session_store.delete_session(agent_type)

    # then
    pass


async def test_list_sessions(session_store: SessionStore) -> None:
    # given
    await session_store.save_session("claude", "session-1")
    await session_store.save_session("opencode", "session-2")

    # when
    sessions = await session_store.list_sessions()

    # then
    assert "claude" in sessions
    assert "opencode" in sessions
    assert sessions["claude"]["session_id"] == "session-1"
    assert sessions["opencode"]["session_id"] == "session-2"
    assert "updated" in sessions["claude"]
    assert "updated" in sessions["opencode"]


async def test_list_sessions_empty(session_store: SessionStore) -> None:
    # given
    # (no sessions saved)

    # when
    sessions = await session_store.list_sessions()

    # then
    assert sessions == {}


async def test_atomic_write_creates_backup(session_store: SessionStore, temp_sessions_dir: Path) -> None:
    # given
    await session_store.save_session("claude", "first-session")
    backup_file = temp_sessions_dir / "sessions.json.bak"

    # when
    await session_store.save_session("opencode", "second-session")

    # then
    assert backup_file.exists()
    backup_content = await anyio.to_thread.run_sync(backup_file.read_text)
    backup_data = json.loads(backup_content)
    assert "claude" in backup_data


async def test_json_format_validity(session_store: SessionStore, temp_sessions_dir: Path) -> None:
    # given
    await session_store.save_session("claude", "test-session")
    sessions_file = temp_sessions_dir / "sessions.json"

    # when
    content = await anyio.to_thread.run_sync(sessions_file.read_text)
    data = json.loads(content)

    # then
    assert isinstance(data, dict)
    assert "claude" in data
    assert "session_id" in data["claude"]
    assert "updated" in data["claude"]
    assert data["claude"]["session_id"] == "test-session"


async def test_corruption_recovery_from_backup(session_store: SessionStore, temp_sessions_dir: Path) -> None:
    # given
    await session_store.save_session("claude", "backup-session")
    # Second save to create backup file
    await session_store.save_session("opencode", "another-session")
    sessions_file = temp_sessions_dir / "sessions.json"

    # Corrupt main file
    await anyio.to_thread.run_sync(sessions_file.write_text, "invalid json{{{")

    # when
    loaded_session = await session_store.get_session("claude")

    # then
    assert loaded_session == "backup-session"


async def test_corruption_recovery_both_files_corrupted(session_store: SessionStore, temp_sessions_dir: Path) -> None:
    # given
    sessions_file = temp_sessions_dir / "sessions.json"
    backup_file = temp_sessions_dir / "sessions.json.bak"

    # Corrupt both files
    await anyio.to_thread.run_sync(sessions_file.write_text, "invalid json{{{")
    await anyio.to_thread.run_sync(backup_file.write_text, "also invalid}}}}")

    # when
    session = await session_store.get_session("claude")

    # then
    assert session is None


async def test_corruption_recovery_start_fresh(
    temp_sessions_dir: Path,
) -> None:
    # given
    sessions_file = temp_sessions_dir / "sessions.json"
    backup_file = temp_sessions_dir / "sessions.json.bak"

    # Create corrupted files
    await anyio.to_thread.run_sync(sessions_file.write_text, "corrupted{{{")
    await anyio.to_thread.run_sync(backup_file.write_text, "corrupted}}}")

    store = SessionStore(base_dir=temp_sessions_dir)

    # when
    await store.save_session("new_agent", "new-session")
    loaded_session = await store.get_session("new_agent")

    # then
    assert loaded_session == "new-session"


async def test_concurrent_access(session_store: SessionStore) -> None:
    # given
    num_operations = 10

    async def save_operation(index: int) -> None:
        await session_store.save_session(f"agent_{index}", f"session_{index}")

    # when
    async with anyio.create_task_group() as tg:
        for i in range(num_operations):
            tg.start_soon(save_operation, i)

    # then
    sessions = await session_store.list_sessions()
    assert len(sessions) == num_operations
    for i in range(num_operations):
        assert f"agent_{i}" in sessions
        assert sessions[f"agent_{i}"]["session_id"] == f"session_{i}"


async def test_concurrent_read_write(session_store: SessionStore) -> None:
    # given
    await session_store.save_session("shared", "initial")

    results: list[str | None] = []

    async def read_operation() -> None:
        session = await session_store.get_session("shared")
        results.append(session)

    async def write_operation(value: str) -> None:
        await session_store.save_session("shared", value)

    # when
    async with anyio.create_task_group() as tg:
        tg.start_soon(write_operation, "updated-1")
        tg.start_soon(read_operation)
        tg.start_soon(write_operation, "updated-2")
        tg.start_soon(read_operation)

    # then
    final_session = await session_store.get_session("shared")
    assert final_session in ["updated-1", "updated-2"]
    assert all(r in ["initial", "updated-1", "updated-2"] for r in results)


async def test_persistence_across_instances(temp_sessions_dir: Path) -> None:
    # given
    store1 = SessionStore(base_dir=temp_sessions_dir)
    await store1.save_session("persistent", "session-data")

    # when
    store2 = SessionStore(base_dir=temp_sessions_dir)
    loaded_session = await store2.get_session("persistent")

    # then
    assert loaded_session == "session-data"


async def test_file_not_exists_initially(temp_sessions_dir: Path) -> None:
    # given
    sessions_file = temp_sessions_dir / "sessions.json"
    assert not sessions_file.exists()

    # when
    store = SessionStore(base_dir=temp_sessions_dir)
    session = await store.get_session("any")

    # then
    assert session is None


async def test_unicode_session_ids(session_store: SessionStore) -> None:
    # given
    unicode_session = "세션-아이디-한글-🚀"

    # when
    await session_store.save_session("unicode_agent", unicode_session)
    loaded_session = await session_store.get_session("unicode_agent")

    # then
    assert loaded_session == unicode_session
