from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sisyphus_core.core.status.manager import StatusManager

pytestmark = [pytest.mark.anyio]


async def test_detect_worktree__if_git_repo__returns_toplevel() -> None:
    # given
    mock_result = AsyncMock()
    mock_result.returncode = 0
    mock_result.stdout = b"/Users/test/repo\n"

    # when
    with patch("sisyphus_core.core.status.manager.anyio.run_process", return_value=mock_result):
        result = await StatusManager.detect_worktree()

    # then
    assert result == Path("/Users/test/repo")


async def test_detect_worktree__if_not_git_repo__returns_cwd() -> None:
    # given
    mock_result = AsyncMock()
    mock_result.returncode = 128

    # when
    with patch("sisyphus_core.core.status.manager.anyio.run_process", return_value=mock_result):
        result = await StatusManager.detect_worktree()

    # then
    assert result == Path.cwd()


async def test_list_all__if_worktrees_exist__returns_list() -> None:
    # given
    StatusManager._worktree_cache = None
    StatusManager._cache_timestamp = None

    mock_result = AsyncMock()
    mock_result.returncode = 0
    mock_result.stdout = b"""worktree /Users/test/main
branch refs/heads/master

worktree /Users/test/feature
branch refs/heads/feature-branch
"""

    # when
    with patch("sisyphus_core.core.status.manager.anyio.run_process", return_value=mock_result):
        result = await StatusManager.list_all()

    # then
    assert len(result) == 2
    assert Path("/Users/test/main") in result
    assert Path("/Users/test/feature") in result


async def test_list_all__if_not_git_repo__returns_empty() -> None:
    # given
    StatusManager._worktree_cache = None
    StatusManager._cache_timestamp = None

    mock_result = AsyncMock()
    mock_result.returncode = 128
    mock_result.stdout = b""

    # when
    with patch("sisyphus_core.core.status.manager.anyio.run_process", return_value=mock_result):
        result = await StatusManager.list_all()

    # then
    assert result == []


async def test_worktree_cache__if_called_twice__uses_cache() -> None:
    # given
    StatusManager._worktree_cache = None
    StatusManager._cache_timestamp = None

    mock_result = AsyncMock()
    mock_result.returncode = 0
    mock_result.stdout = b"worktree /Users/test/main\n"

    # when
    with patch("sisyphus_core.core.status.manager.anyio.run_process", return_value=mock_result) as mock_run:
        _ = await StatusManager.list_all()
        _ = await StatusManager.list_all()

    # then
    assert mock_run.call_count == 1


async def test_worktree_cache__if_expired__refreshes() -> None:
    # given
    StatusManager._worktree_cache = {Path("/old"): []}
    StatusManager._cache_timestamp = 0.0

    mock_result = AsyncMock()
    mock_result.returncode = 0
    mock_result.stdout = b"worktree /Users/test/new\n"

    # when
    with patch("sisyphus_core.core.status.manager.anyio.run_process", return_value=mock_result):
        with patch("time.time", return_value=100.0):
            result = await StatusManager.list_all()

    # then
    assert Path("/Users/test/new") in result
    assert Path("/old") not in result


async def test_is_cache_expired__if_no_cache__returns_true() -> None:
    # given
    StatusManager._cache_timestamp = None

    # when
    result = StatusManager._is_cache_expired()

    # then
    assert result is True


async def test_is_cache_expired__if_within_ttl__returns_false() -> None:
    # given
    StatusManager._cache_timestamp = 100.0

    # when
    with patch("time.time", return_value=150.0):
        result = StatusManager._is_cache_expired()

    # then
    assert result is False


async def test_is_cache_expired__if_beyond_ttl__returns_true() -> None:
    # given
    StatusManager._cache_timestamp = 100.0

    # when
    with patch("time.time", return_value=200.0):
        result = StatusManager._is_cache_expired()

    # then
    assert result is True


async def test_refresh_worktree_cache__if_success__updates_cache() -> None:
    # given
    StatusManager._worktree_cache = None
    StatusManager._cache_timestamp = None

    mock_result = AsyncMock()
    mock_result.returncode = 0
    mock_result.stdout = b"""worktree /Users/test/main
branch refs/heads/master
"""

    # when
    with patch("sisyphus_core.core.status.manager.anyio.run_process", return_value=mock_result):
        with patch("time.time", return_value=100.0):
            await StatusManager._refresh_worktree_cache()

    # then
    assert StatusManager._worktree_cache is not None
    assert Path("/Users/test/main") in StatusManager._worktree_cache
    assert StatusManager._cache_timestamp == 100.0


async def test_refresh_worktree_cache__if_git_fails__sets_empty_cache() -> None:
    # given
    StatusManager._worktree_cache = None
    StatusManager._cache_timestamp = None

    mock_result = AsyncMock()
    mock_result.returncode = 128
    mock_result.stdout = b""

    # when
    with patch("sisyphus_core.core.status.manager.anyio.run_process", return_value=mock_result):
        with patch("time.time", return_value=100.0):
            await StatusManager._refresh_worktree_cache()

    # then
    assert StatusManager._worktree_cache == {}
    assert StatusManager._cache_timestamp == 100.0
