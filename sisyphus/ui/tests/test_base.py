from __future__ import annotations

import pytest

from sisyphus.ui.base import UIProtocol, create_ui
from sisyphus.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


class MockUI:
    async def initialize(self) -> None:
        pass

    async def show_message(self, message: AgentMessage, source: str) -> None:
        pass

    async def show_status(self, status: str) -> None:
        pass

    async def get_input(self) -> str | None:
        return None

    async def close(self) -> None:
        pass


class IncompleteUI:
    async def initialize(self) -> None:
        pass


async def test_protocol_validation_complete() -> None:
    # Given
    ui = MockUI()

    # When/Then
    assert isinstance(ui, UIProtocol)


async def test_protocol_validation_incomplete() -> None:
    # Given
    ui = IncompleteUI()

    # When/Then
    assert not isinstance(ui, UIProtocol)


async def test_mock_ui_initialize() -> None:
    # Given
    ui = MockUI()

    # When
    await ui.initialize()

    # Then


async def test_mock_ui_show_message() -> None:
    # Given
    ui = MockUI()
    message = AgentMessage(role="assistant", content="test")

    # When
    await ui.show_message(message, "execute")

    # Then


async def test_mock_ui_show_status() -> None:
    # Given
    ui = MockUI()

    # When
    await ui.show_status("Processing...")

    # Then


async def test_mock_ui_get_input() -> None:
    # Given
    ui = MockUI()

    # When
    result = await ui.get_input()

    # Then
    assert result is None


async def test_mock_ui_close() -> None:
    # Given
    ui = MockUI()

    # When
    await ui.close()

    # Then


def test_create_ui_factory_signature() -> None:
    # Given/When/Then
    assert callable(create_ui)
