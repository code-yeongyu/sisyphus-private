"""Agent Protocol definition for Sisyphus."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sisyphus.utils.types import AgentMessage


@runtime_checkable
class Agent(Protocol):
    """모든 에이전트가 구현해야 하는 프로토콜."""

    supports_interactive: bool

    async def initialize(self) -> None:
        """에이전트 초기화."""
        ...

    async def start_session(self, session_id: str | None = None) -> str:
        """세션 시작 또는 재개, 실제 세션 ID 반환."""
        ...

    async def send(self, message: str) -> None:
        """메시지 전송."""
        ...

    async def stream(self) -> AsyncIterator[AgentMessage]:
        """응답 스트리밍."""
        ...

    async def close(self) -> None:
        """정리."""
        ...
