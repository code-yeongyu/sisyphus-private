from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import pytest

from sisyphus_core.core.session import SessionStore

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = [pytest.mark.anyio]


@pytest.fixture()
async def temp_worktree_dir(tmp_path: Path) -> AsyncIterator[Path]:
    # given
    worktree_dir = tmp_path / "worktree"
    worktree_dir.mkdir()

    git_dir = worktree_dir / ".git"
    git_dir.mkdir()

    yield worktree_dir

    # cleanup
    if worktree_dir.exists():
        await anyio.to_thread.run_sync(shutil.rmtree, worktree_dir)


@pytest.fixture()
async def sisyphus_sessions_dir(temp_worktree_dir: Path) -> Path:
    # given
    sessions_dir = temp_worktree_dir / ".sisyphus" / "sessions"
    sessions_dir.mkdir(parents=True)
    return sessions_dir


@pytest.fixture()
async def session_store_sisyphus(sisyphus_sessions_dir: Path) -> SessionStore:
    # given
    return SessionStore(base_dir=sisyphus_sessions_dir)


async def test_session_store__if_initialized_with_sisyphus_path__uses_correct_directory(
    sisyphus_sessions_dir: Path,
) -> None:
    # given
    store = SessionStore(base_dir=sisyphus_sessions_dir)

    # when
    # (initialization happens in constructor)

    # then
    assert store.base_dir == sisyphus_sessions_dir
    assert store.sessions_file == sisyphus_sessions_dir / "sessions.json"
    assert store.backup_file == sisyphus_sessions_dir / "sessions.json.bak"
    assert sisyphus_sessions_dir.exists()


async def test_session_store__if_save_and_load__stores_in_sisyphus_directory(
    session_store_sisyphus: SessionStore,
    sisyphus_sessions_dir: Path,
) -> None:
    # given
    agent_type = "claude"
    session_id = "test-session-123"
    plan_id = "default"

    # when
    await session_store_sisyphus.save_session(agent_type, session_id, plan_id)
    loaded_session = await session_store_sisyphus.get_session(agent_type, plan_id)

    # then
    assert loaded_session == session_id
    assert (sisyphus_sessions_dir / "sessions.json").exists()


async def test_session_store__if_multiple_agents__separates_sessions_correctly(
    session_store_sisyphus: SessionStore,
) -> None:
    # given
    claude_session = "claude-session-456"
    opencode_session = "opencode-session-789"
    plan_id = "default"

    # when
    await session_store_sisyphus.save_session("claude", claude_session, plan_id)
    await session_store_sisyphus.save_session("opencode", opencode_session, plan_id)

    # then
    assert await session_store_sisyphus.get_session("claude", plan_id) == claude_session
    assert await session_store_sisyphus.get_session("opencode", plan_id) == opencode_session


async def test_session_store__if_corrupted_file__recovers_from_backup(
    session_store_sisyphus: SessionStore,
    sisyphus_sessions_dir: Path,
) -> None:
    # given
    plan_id = "default"
    await session_store_sisyphus.save_session("claude", "backup-session", plan_id)
    await session_store_sisyphus.save_session("opencode", "another-session", plan_id)
    sessions_file = sisyphus_sessions_dir / "sessions.json"

    # Corrupt main file
    await anyio.to_thread.run_sync(sessions_file.write_text, "invalid json{{{")

    # when
    loaded_session = await session_store_sisyphus.get_session("claude", plan_id)

    # then
    assert loaded_session == "backup-session"


async def test_session_store__if_default_init__uses_cwd_and_creates_sisyphus_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given
    cwd_root = tmp_path / "project-dir"
    cwd_root.mkdir()
    monkeypatch.chdir(cwd_root)

    # when
    store = SessionStore()

    # then
    expected_dir = cwd_root / ".sisyphus" / "sessions"
    assert store.base_dir == expected_dir
    assert expected_dir.exists()


async def test_session_store__if_persisted_across_instances__maintains_data(
    sisyphus_sessions_dir: Path,
) -> None:
    # given
    plan_id = "default"
    store1 = SessionStore(base_dir=sisyphus_sessions_dir)
    await store1.save_session("persistent", "session-data", plan_id)

    # when
    store2 = SessionStore(base_dir=sisyphus_sessions_dir)
    loaded_session = await store2.get_session("persistent", plan_id)

    # then
    assert loaded_session == "session-data"


async def test_session_store__if_atomic_write__creates_backup_file(
    session_store_sisyphus: SessionStore,
    sisyphus_sessions_dir: Path,
) -> None:
    # given
    plan_id = "default"
    await session_store_sisyphus.save_session("claude", "first-session", plan_id)
    backup_file = sisyphus_sessions_dir / "sessions.json.bak"

    # when
    await session_store_sisyphus.save_session("opencode", "second-session", plan_id)

    # then
    assert backup_file.exists()
    backup_content = await anyio.to_thread.run_sync(backup_file.read_text)
    backup_data = json.loads(backup_content)
    assert "claude" in backup_data


async def test_session_store__if_deleted__removes_from_sisyphus_directory(
    session_store_sisyphus: SessionStore,
) -> None:
    # given
    agent_type = "opencode"
    session_id = "session-to-delete"
    plan_id = "default"
    await session_store_sisyphus.save_session(agent_type, session_id, plan_id)

    # when
    await session_store_sisyphus.delete_session(agent_type, plan_id)
    loaded_session = await session_store_sisyphus.get_session(agent_type, plan_id)

    # then
    assert loaded_session is None


async def test_session_store__if_list_sessions__returns_all_stored_sessions(
    session_store_sisyphus: SessionStore,
) -> None:
    # given
    plan_id = "default"
    await session_store_sisyphus.save_session("claude", "session-1", plan_id)
    await session_store_sisyphus.save_session("opencode", "session-2", plan_id)

    # when
    sessions = await session_store_sisyphus.list_sessions()

    # then
    assert "claude" in sessions
    assert "opencode" in sessions
    assert sessions["claude"][plan_id]["session_id"] == "session-1"
    assert sessions["opencode"][plan_id]["session_id"] == "session-2"
    assert "updated" in sessions["claude"][plan_id]
    assert "updated" in sessions["opencode"][plan_id]
