"""UI Protocol definition and factory function."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sisyphus.utils.types import AgentMessage


@runtime_checkable
class UIProtocol(Protocol):
    """UI 구현이 따라야 할 프로토콜."""

    async def initialize(self) -> None:
        """UI 초기화."""
        ...

    async def show_message(self, message: AgentMessage, source: str) -> None:
        """메시지 표시 (source: 'execute' or 'verify')."""
        ...

    async def show_status(self, status: str) -> None:
        """상태 메시지 표시."""
        ...

    async def get_input(self) -> str | None:
        """사용자 입력 받기 (TUI only, CLI는 None 반환)."""
        ...

    async def close(self) -> None:
        """UI 종료."""
        ...


def create_ui(mode: str) -> UIProtocol:
    """UI 팩토리.

    Args:
        mode: UI 모드 ('tui' 또는 'cli')

    Returns:
        UIProtocol을 구현하는 UI 인스턴스
    """
    if mode == "tui":
        from sisyphus.ui.tui import TUI

        return TUI()
    else:
        from sisyphus.ui.cli import CLI

        return CLI()
