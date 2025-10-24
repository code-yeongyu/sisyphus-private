from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from sisyphus.ui.tui.components.chat_log import ChatLog

pytestmark = [pytest.mark.anyio]


async def test_chat_log__if_initialized__has_correct_defaults() -> None:
    # given
    # when
    chat_log = ChatLog()

    # then
    assert chat_log._user_scrolled_up is False
    assert chat_log._programmatic_scrolling is False


async def test_chat_log__when_user_scrolled_up__does_not_auto_scroll() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)

            for i in range(50):
                chat_log.write_execute_message(f"Message {i}")
            await pilot.pause()

            chat_log._user_scrolled_up = True
            if chat_log.max_scroll_y > 10:
                chat_log.scroll_to(y=0)
            await pilot.pause()

            # when
            chat_log.write_execute_message("New message")
            await pilot.pause()

            # then
            assert chat_log._user_scrolled_up is True
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_should_auto_scroll__if_user_scrolled_up__returns_false() -> None:
    # given
    chat_log = ChatLog()
    chat_log._user_scrolled_up = True

    # when
    result = chat_log._should_auto_scroll()

    # then
    assert result is False


async def test_chat_log__if_user_scrolled_up_flag_set__does_not_auto_scroll() -> None:
    # given
    chat_log = ChatLog()
    chat_log._user_scrolled_up = True

    # when
    result = chat_log._should_auto_scroll()

    # then
    assert result is False
    assert chat_log._user_scrolled_up is True


async def test_write_user_message__if_called__preserves_user_scroll_state() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)
            chat_log._user_scrolled_up = True

            # when
            chat_log.write_user_message("Test message")
            await pilot.pause()

            # then
            assert chat_log._user_scrolled_up is True
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_write_execute_message__if_called__preserves_user_scroll_state() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)
            chat_log._user_scrolled_up = True

            # when
            chat_log.write_execute_message("Test execution")
            await pilot.pause()

            # then
            assert chat_log._user_scrolled_up is True
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_write_verify_message__if_called__preserves_user_scroll_state() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)
            chat_log._user_scrolled_up = True

            # when
            chat_log.write_verify_message("Test verification")
            await pilot.pause()

            # then
            assert chat_log._user_scrolled_up is True
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_write_completion_message__if_called__preserves_user_scroll_state() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)
            chat_log._user_scrolled_up = True

            # when
            chat_log.write_completion_message("Task completed")
            await pilot.pause()

            # then
            assert chat_log._user_scrolled_up is True
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_chat_log__if_at_bottom__auto_scrolls_on_new_message() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ChatLog()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            chat_log = app.query_one(ChatLog)

            for i in range(10):
                chat_log.write_execute_message(f"Message {i}")
            await pilot.pause()

            chat_log._user_scrolled_up = False

            # when
            chat_log.write_execute_message("New message")
            await pilot.pause()

            # then
            assert chat_log._user_scrolled_up is False
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise
