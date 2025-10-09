"""TUI tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sisyphus.ui.base import UIProtocol
from sisyphus.ui.tui.app import TUI
from sisyphus.ui.tui.components.chat_log import ChatLog
from sisyphus.ui.tui.components.status_panel import StatusPanel
from sisyphus.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio()]


async def test_tui_protocol_compliance() -> None:
    """TUI가 UIProtocol을 만족하는지 검증."""
    # given
    tui = TUI()

    # when / then
    assert isinstance(tui, UIProtocol)


async def test_tui_initialize() -> None:
    """TUI 초기화 테스트."""
    # given
    tui = TUI()
    assert tui._initialized is False

    # when
    await tui.initialize()

    # then
    assert tui._initialized is True


async def test_tui_show_message_execute() -> None:
    """Execute 메시지 표시 테스트."""
    # given
    tui = TUI()
    message = AgentMessage(role="assistant", content="Test execute content")

    mock_chat_log = MagicMock(spec=ChatLog)

    # when
    with patch.object(tui, "query_one", return_value=mock_chat_log):
        await tui.show_message(message, "execute")

    # then
    mock_chat_log.write_execute_message.assert_called_once_with("Test execute content")


async def test_tui_show_message_verify() -> None:
    """Verify 메시지 표시 테스트."""
    # given
    tui = TUI()
    message = AgentMessage(role="assistant", content="Test verify content")

    mock_chat_log = MagicMock(spec=ChatLog)

    # when
    with patch.object(tui, "query_one", return_value=mock_chat_log):
        await tui.show_message(message, "verify")

    # then
    mock_chat_log.write_verify_message.assert_called_once_with("Test verify content")


async def test_tui_show_message_with_metadata() -> None:
    """메타데이터를 포함한 메시지 표시 테스트."""
    # given
    tui = TUI()
    message = AgentMessage(
        role="assistant",
        content="Test content with metadata",
        metadata={"session_id": "test-123", "timestamp": "2025-10-09"},
    )

    mock_chat_log = MagicMock(spec=ChatLog)

    # when
    with patch.object(tui, "query_one", return_value=mock_chat_log):
        await tui.show_message(message, "execute")

    # then
    mock_chat_log.write_execute_message.assert_called_once_with("Test content with metadata")


async def test_tui_show_status() -> None:
    """상태 표시 테스트."""
    # given
    tui = TUI()
    status_text = "Processing task 1/5"

    mock_status_panel = MagicMock(spec=StatusPanel)

    # when
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui.show_status(status_text)

    # then
    mock_status_panel.update_status.assert_called_once_with(status_text)


async def test_tui_get_input_from_queue() -> None:
    """메시지 큐에서 입력 가져오기 테스트."""
    # given
    tui = TUI()

    # on_mount 시뮬레이션: 메시지 큐 생성
    await tui.on_mount()

    # when
    # 메시지 큐에 입력 추가
    if tui._send_stream:
        await tui._send_stream.send("Test user input")

    result = await tui.get_input()

    # then
    assert result == "Test user input"


async def test_tui_get_input_returns_none_when_no_stream() -> None:
    """스트림이 없을 때 None 반환 테스트."""
    # given
    tui = TUI()
    assert tui._receive_stream is None

    # when
    result = await tui.get_input()

    # then
    assert result is None


async def test_tui_components_separated() -> None:
    """컴포넌트가 분리되어 있는지 검증."""
    # given
    tui = TUI()

    # when
    composition = list(tui.compose())

    # then
    # compose()가 레이아웃을 yield하는지 확인
    assert len(composition) > 0


async def test_tui_ctrl_c_once() -> None:
    """Ctrl+C 한 번 누를 시 경고 표시."""
    # given
    tui = TUI()
    mock_status_panel = MagicMock(spec=StatusPanel)

    # when
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui._handle_interrupt()

    # then
    assert tui.ctrl_c_count == 1
    assert tui.last_ctrl_c_time is not None
    mock_status_panel.update_status.assert_called_once_with("⚠️ Ctrl+C 한 번 더 누르면 종료됩니다")


async def test_tui_ctrl_c_twice() -> None:
    """Ctrl+C 2회 (1초 내) 누를 시 종료."""
    # given
    tui = TUI()
    mock_status_panel = MagicMock(spec=StatusPanel)

    # 첫 번째 Ctrl+C
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui._handle_interrupt()

    assert tui.ctrl_c_count == 1

    # when: 두 번째 Ctrl+C (1초 내)
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        with patch.object(tui, "exit") as mock_exit:
            await tui._handle_interrupt()

    # then
    assert tui.ctrl_c_count == 2
    assert tui.shutdown_event.is_set()
    mock_exit.assert_called_once()


async def test_tui_ctrl_c_reset() -> None:
    """Ctrl+C 후 1초 이상 경과 시 카운터 리셋."""
    # given
    tui = TUI()
    mock_status_panel = MagicMock(spec=StatusPanel)

    # 첫 번째 Ctrl+C
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui._handle_interrupt()

    assert tui.ctrl_c_count == 1
    first_time = tui.last_ctrl_c_time

    # when: 1초 이상 경과 후 Ctrl+C
    # last_ctrl_c_time을 1초 이상 전으로 설정
    tui.last_ctrl_c_time = datetime.now() - timedelta(seconds=2)

    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui._handle_interrupt()

    # then
    # 카운터가 리셋되어 1로 돌아감
    assert tui.ctrl_c_count == 1
    assert tui.last_ctrl_c_time is not None
    assert tui.last_ctrl_c_time != first_time


async def test_tui_message_queue_created() -> None:
    """on_mount 시 메시지 큐가 생성되는지 검증."""
    # given
    tui = TUI()
    assert tui._send_stream is None
    assert tui._receive_stream is None

    # when
    await tui.on_mount()

    # then
    assert tui._send_stream is not None
    assert tui._receive_stream is not None


async def test_tui_message_queue_send_receive() -> None:
    """메시지 큐 send/receive가 작동하는지 검증."""
    # given
    tui = TUI()
    await tui.on_mount()

    # when
    if tui._send_stream:
        await tui._send_stream.send("Message 1")
        await tui._send_stream.send("Message 2")

    # then
    msg1 = await tui.get_input()
    msg2 = await tui.get_input()

    assert msg1 == "Message 1"
    assert msg2 == "Message 2"


async def test_tui_safe_shutdown() -> None:
    """안전한 종료 절차 테스트."""
    # given
    tui = TUI()
    await tui.on_mount()

    mock_status_panel = MagicMock(spec=StatusPanel)

    # when
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        with patch.object(tui, "exit") as mock_exit:
            await tui._safe_shutdown()

    # then
    # 스트림이 닫혔는지 확인 (aclose 호출됨)
    # shutdown_event가 설정되었는지 확인
    assert tui.shutdown_event.is_set()
    mock_exit.assert_called_once()
    mock_status_panel.update_status.assert_called_once_with("🔄 종료 중...")


async def test_tui_close_calls_shutdown() -> None:
    """close()가 _safe_shutdown()을 호출하는지 검증."""
    # given
    tui = TUI()
    await tui.on_mount()

    # when
    with patch.object(tui, "_safe_shutdown", new_callable=AsyncMock) as mock_shutdown:
        await tui.close()

    # then
    mock_shutdown.assert_called_once()


async def test_tui_full_lifecycle() -> None:
    """전체 라이프사이클 테스트."""
    # given
    tui = TUI()

    # when/then: initialize
    await tui.initialize()
    assert tui._initialized is True

    # when/then: on_mount
    await tui.on_mount()
    assert tui._send_stream is not None
    assert tui._receive_stream is not None

    # when/then: show message
    mock_chat_log = MagicMock(spec=ChatLog)
    with patch.object(tui, "query_one", return_value=mock_chat_log):
        msg1 = AgentMessage(role="user", content="Execute message")
        await tui.show_message(msg1, "execute")

    mock_chat_log.write_execute_message.assert_called_once()

    # when/then: show status
    mock_status_panel = MagicMock(spec=StatusPanel)
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui.show_status("Status update")

    mock_status_panel.update_status.assert_called_once()

    # when/then: send and get input
    if tui._send_stream:
        await tui._send_stream.send("Test input")
    user_input = await tui.get_input()
    assert user_input == "Test input"

    # when/then: close
    with patch.object(tui, "exit"):
        with patch.object(tui, "query_one", return_value=mock_status_panel):
            await tui.close()

    assert tui.shutdown_event.is_set()


async def test_tui_multiple_messages_sequence() -> None:
    """여러 메시지 순차 표시 테스트."""
    # given
    tui = TUI()
    messages = [
        (AgentMessage(role="user", content="Message 1"), "execute"),
        (AgentMessage(role="assistant", content="Message 2"), "verify"),
        (AgentMessage(role="user", content="Message 3"), "execute"),
    ]

    mock_chat_log = MagicMock(spec=ChatLog)

    # when
    with patch.object(tui, "query_one", return_value=mock_chat_log):
        for msg, source in messages:
            await tui.show_message(msg, source)

    # then
    assert mock_chat_log.write_execute_message.call_count == 2
    assert mock_chat_log.write_verify_message.call_count == 1


async def test_tui_empty_message_content() -> None:
    """빈 메시지 내용 처리 테스트."""
    # given
    tui = TUI()
    message = AgentMessage(role="assistant", content="")

    mock_chat_log = MagicMock(spec=ChatLog)

    # when
    with patch.object(tui, "query_one", return_value=mock_chat_log):
        await tui.show_message(message, "execute")

    # then
    mock_chat_log.write_execute_message.assert_called_once_with("")
