from __future__ import annotations

from unittest.mock import Mock

import pytest
from textual.app import App, ComposeResult

from sisyphus.ui.tui.components.input_bar import InputBar

pytestmark = [pytest.mark.anyio]


async def test_on_key__if_enter_pressed__sends_message() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield InputBar()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            input_bar = app.query_one(InputBar)
            input_bar.text = "hello"
            input_bar.app.query_one = Mock(return_value=Mock(write_user_message=Mock()))

            # when
            await pilot.press("enter")

            # then
            assert input_bar._queued_message == "hello"
            assert input_bar.text == ""
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_on_key__if_shift_enter_pressed__does_not_send_message() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield InputBar()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            input_bar = app.query_one(InputBar)
            input_bar.text = "hello"

            # when
            await pilot.press("shift+enter")

            # then
            assert input_bar._queued_message == ""
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_on_key__if_up_pressed_with_queue__loads_queue() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield InputBar()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            input_bar = app.query_one(InputBar)
            input_bar._queued_message = "queued message"
            input_bar.text = ""

            # when
            await pilot.press("up")

            # then
            assert input_bar.text == "queued message"
            assert input_bar._queued_message == ""
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_on_key__if_escape_pressed__pauses_agent() -> None:
    # given
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield InputBar()

    app = TestApp()
    try:
        async with app.run_test() as pilot:
            input_bar = app.query_one(InputBar)
            input_bar._agent_paused = False

            # when
            await pilot.press("escape")

            # then
            assert input_bar._agent_paused is True
            assert "paused" in input_bar.suggestion.lower()
    except RuntimeError as e:
        if "no running event loop" in str(e):
            pytest.skip("Textual requires asyncio")
        raise


async def test_input_bar__if_initialized__has_correct_defaults() -> None:
    # given
    # when
    input_bar = InputBar()

    # then
    assert input_bar._queued_message == ""
    assert input_bar._last_sent == ""
    assert input_bar._agent_paused is False
    assert "pause" in input_bar.suggestion.lower()


async def test_get_and_clear_queue__if_has_queued_message__returns_and_clears() -> None:
    # given
    input_bar = InputBar()
    input_bar._queued_message = "Test message"

    # when
    result = input_bar.get_and_clear_queue()

    # then
    assert result == "Test message"
    assert input_bar._queued_message == ""
    assert input_bar._last_sent == "Test message"


async def test_get_and_clear_queue__if_empty_queue__returns_none() -> None:
    # given
    input_bar = InputBar()
    input_bar._queued_message = ""

    # when
    result = input_bar.get_and_clear_queue()

    # then
    assert result is None


async def test_update_suggestion__if_has_queued_message__shows_preview() -> None:
    # given
    input_bar = InputBar()
    input_bar._queued_message = "This is a very long message that should be truncated"

    # when
    input_bar._update_suggestion()

    # then
    assert "Queued:" in input_bar.suggestion
    assert "UP" in input_bar.suggestion


async def test_update_suggestion__if_no_queue__shows_original() -> None:
    # given
    input_bar = InputBar()
    input_bar._queued_message = ""
    original = input_bar._original_suggestion

    # when
    input_bar._update_suggestion()

    # then
    assert input_bar.suggestion == original
