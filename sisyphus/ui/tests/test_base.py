from __future__ import annotations

import pytest

from sisyphus.ui.base import UIProtocol, create_ui
from sisyphus.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


class MockUI:
    """완전한 UIProtocol 구현 (테스트용)."""

    def __init__(self) -> None:
        self.messages: list[tuple[AgentMessage, str]] = []
        self.statuses: list[str] = []
        self.inputs: list[str | None] = ["test_input", None]
        self.input_index: int = 0
        self.initialized: bool = False

    async def initialize(self) -> None:
        """UI 초기화."""
        self.initialized = True

    async def show_message(self, message: AgentMessage, source: str) -> None:
        """메시지 표시."""
        self.messages.append((message, source))

    async def show_status(self, status: str) -> None:
        """상태 메시지 표시."""
        self.statuses.append(status)

    async def get_input(self) -> str | None:
        """사용자 입력 받기."""
        if self.input_index >= len(self.inputs):
            return None
        result = self.inputs[self.input_index]
        self.input_index += 1
        return result


class IncompleteUI:
    """불완전한 UI 구현 (일부 메서드만 구현)."""

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
    assert not ui.initialized

    # When
    await ui.initialize()

    # Then
    assert ui.initialized


async def test_mock_ui_show_message() -> None:
    # Given
    ui = MockUI()
    message = AgentMessage(role="assistant", content="test")

    # When
    await ui.show_message(message, "execute")

    # Then
    assert len(ui.messages) == 1
    assert ui.messages[0] == (message, "execute")


async def test_mock_ui_show_status() -> None:
    # Given
    ui = MockUI()

    # When
    await ui.show_status("Processing...")

    # Then
    assert len(ui.statuses) == 1
    assert ui.statuses[0] == "Processing..."


async def test_mock_ui_get_input() -> None:
    # Given
    ui = MockUI()

    # When
    result1 = await ui.get_input()
    result2 = await ui.get_input()
    result3 = await ui.get_input()

    # Then
    assert result1 == "test_input"
    assert result2 is None
    assert result3 is None


async def test_mock_ui_multiple_messages() -> None:
    # Given
    ui = MockUI()
    msg1 = AgentMessage(role="user", content="첫 메시지")
    msg2 = AgentMessage(role="assistant", content="두 번째 메시지")

    # When
    await ui.show_message(msg1, "execute")
    await ui.show_message(msg2, "verify")

    # Then
    assert len(ui.messages) == 2
    assert ui.messages[0] == (msg1, "execute")
    assert ui.messages[1] == (msg2, "verify")


async def test_mock_ui_multiple_statuses() -> None:
    # Given
    ui = MockUI()

    # When
    await ui.show_status("상태 1")
    await ui.show_status("상태 2")
    await ui.show_status("상태 3")

    # Then
    assert len(ui.statuses) == 3
    assert ui.statuses == ["상태 1", "상태 2", "상태 3"]


def test_create_ui_factory_signature() -> None:
    # Given/When/Then
    assert callable(create_ui)
