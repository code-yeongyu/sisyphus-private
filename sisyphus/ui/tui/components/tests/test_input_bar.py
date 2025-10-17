from __future__ import annotations

import pytest

from sisyphus.ui.tui.components.input_bar import InputBar

pytestmark = [pytest.mark.anyio]


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
