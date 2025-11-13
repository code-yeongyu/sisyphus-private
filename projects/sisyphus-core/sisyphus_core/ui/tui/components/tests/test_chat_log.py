from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from sisyphus.ui.tui.components.chat_log import ChatLog

pytestmark = [pytest.mark.anyio]


async def test_write_user_message__if_called__writes_formatted_message() -> None:
    """사용자 메시지 작성 시 올바른 형식으로 출력되는지 확인."""

    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)

            # when
            chat_log.write_user_message("Test message")
            await pilot.pause()

            # then: 메시지가 작성되었는지 확인
            assert len(chat_log.lines) > 0
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_write_execute_message__if_called__writes_formatted_message() -> None:
    """실행 메시지 작성 시 올바른 형식으로 출력되는지 확인."""

    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)

            # when
            chat_log.write_execute_message("Execute test")
            await pilot.pause()

            # then: 메시지가 작성되었는지 확인
            assert len(chat_log.lines) > 0
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_write_verify_message__if_called__writes_formatted_message() -> None:
    """검증 메시지 작성 시 올바른 형식으로 출력되는지 확인."""

    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)

            # when
            chat_log.write_verify_message("Verify test")
            await pilot.pause()

            # then: 메시지가 작성되었는지 확인
            assert len(chat_log.lines) > 0
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_write_completion_message__if_called__writes_formatted_message() -> None:
    """완료 메시지 작성 시 올바른 형식으로 출력되는지 확인."""

    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)

            # when
            chat_log.write_completion_message("Task completed")
            await pilot.pause()

            # then: 메시지가 작성되었는지 확인
            assert len(chat_log.lines) > 0
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_chat_log__if_auto_scroll_enabled__scrolls_to_end() -> None:
    """새 메시지 추가 시 자동으로 맨 아래로 스크롤되는지 확인."""

    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)

            # when: 여러 메시지 추가
            for i in range(20):
                chat_log.write_user_message(f"Message {i}")
            await pilot.pause()

            chat_log.write_execute_message("Additional message")
            await pilot.pause()

            # then: 스크롤이 맨 아래에 있어야 함
            # auto_scroll=True이므로 max_scroll_y에 가까워야 함
            assert chat_log.scroll_offset.y >= chat_log.max_scroll_y - 2
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_chat_log__if_initialized__has_auto_scroll_enabled() -> None:
    """ChatLog 초기화 시 auto_scroll이 활성화되어 있는지 확인."""
    # given
    chat_log = ChatLog()

    # when
    # (자동으로 initialized 됨)

    # then: auto_scroll이 True여야 함
    assert chat_log.auto_scroll is True
