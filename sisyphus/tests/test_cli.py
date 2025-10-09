"""CLI integration tests for sisyphus/cli.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from sisyphus.agents.base import Agent
from sisyphus.agents.claude import ClaudeAgent
from sisyphus.agents.droid import DroidAgent
from sisyphus.agents.opencode import OpenCodeAgent
from sisyphus.cli import create_agent, resolve_binary, run, validate_url

pytestmark = [pytest.mark.anyio()]


async def test_validate_url_valid_http() -> None:
    """Valid HTTP URL 검증."""
    # given
    url = "http://localhost:8080"

    # when
    result = validate_url(url)

    # then
    assert result == url


async def test_validate_url_valid_https() -> None:
    """Valid HTTPS URL 검증."""
    # given
    url = "https://example.com:3000/api"

    # when
    result = validate_url(url)

    # then
    assert result == url


async def test_validate_url_invalid_no_scheme() -> None:
    """스킴이 없는 잘못된 URL."""
    # given
    url = "localhost:8080"

    # when/then
    with pytest.raises(typer.BadParameter, match="Invalid URL"):
        validate_url(url)


async def test_validate_url_invalid_no_netloc() -> None:
    """netloc이 없는 잘못된 URL."""
    # given
    url = "http://"

    # when/then
    with pytest.raises(typer.BadParameter, match="Invalid URL"):
        validate_url(url)


async def test_resolve_binary_specific_priority() -> None:
    """specific 바이너리가 우선순위를 갖는다."""
    # given
    common = Path("/common/binary")
    specific = Path("/specific/binary")

    # when
    result = resolve_binary(common, specific)

    # then
    assert result == specific


async def test_resolve_binary_common_fallback() -> None:
    """specific이 None이면 common 사용."""
    # given
    common = Path("/common/binary")
    specific = None

    # when
    result = resolve_binary(common, specific)

    # then
    assert result == common


async def test_resolve_binary_both_none() -> None:
    """둘 다 None이면 None 반환."""
    # given
    common = None
    specific = None

    # when
    result = resolve_binary(common, specific)

    # then
    assert result is None


async def test_create_agent_claude_without_model() -> None:
    """Claude 에이전트 생성 (모델 없음)."""
    # given
    agent_spec = "claude"
    sdk_options_json = None
    binary_path = None
    opencode_url = None

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, ClaudeAgent)
    assert isinstance(agent, Agent)


async def test_create_agent_claude_with_model() -> None:
    """Claude 에이전트 생성 (모델 포함)."""
    # given
    agent_spec = "claude:sonnet"
    sdk_options_json = None
    binary_path = None
    opencode_url = None

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, ClaudeAgent)
    assert agent._model == "sonnet"


async def test_create_agent_claude_with_sdk_options() -> None:
    """Claude 에이전트 생성 (SDK 옵션 포함)."""
    # given
    agent_spec = "claude"
    sdk_options_json = '{"temperature": 0.5, "max_tokens": 1000}'
    binary_path = None
    opencode_url = None

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, ClaudeAgent)
    assert agent._sdk_options["temperature"] == 0.5
    assert agent._sdk_options["max_tokens"] == 1000


async def test_create_agent_droid_without_model() -> None:
    """Droid 에이전트 생성 (모델 없음)."""
    # given
    agent_spec = "droid"
    sdk_options_json = None
    binary_path = Path("/path/to/droid")
    opencode_url = None

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, DroidAgent)
    assert agent._binary == binary_path


async def test_create_agent_droid_with_model() -> None:
    """Droid 에이전트 생성 (모델 포함)."""
    # given
    agent_spec = "droid:gpt-5"
    sdk_options_json = None
    binary_path = None
    opencode_url = None

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, DroidAgent)
    assert agent._model == "gpt-5"


async def test_create_agent_opencode() -> None:
    """OpenCode 에이전트 생성."""
    # given
    agent_spec = "opencode"
    sdk_options_json = None
    binary_path = None
    opencode_url = "http://localhost:8080"

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, OpenCodeAgent)
    assert agent._server_url == opencode_url


async def test_create_agent_unknown_type() -> None:
    """알 수 없는 에이전트 타입."""
    # given
    agent_spec = "unknown-agent"
    sdk_options_json = None
    binary_path = None
    opencode_url = None

    # when/then
    with pytest.raises(typer.BadParameter, match="Unknown agent type"):
        create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)


async def test_create_agent_invalid_json() -> None:
    """잘못된 JSON SDK 옵션."""
    # given
    agent_spec = "claude"
    sdk_options_json = '{"invalid": json}'
    binary_path = None
    opencode_url = None

    # when/then
    with pytest.raises(typer.BadParameter, match="Invalid JSON in SDK options"):
        create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)


async def test_create_agent_json_with_model_override() -> None:
    """SDK 옵션 JSON에 모델이 있을 때 agent_spec의 모델로 오버라이드."""
    # given
    agent_spec = "claude:sonnet-4"
    sdk_options_json = '{"model": "old-model", "temperature": 0.7}'
    binary_path = None
    opencode_url = None

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, ClaudeAgent)
    # agent_spec의 모델이 sdk_options에 추가됨
    assert agent._sdk_options["model"] == "sonnet-4"
    assert agent._sdk_options["temperature"] == 0.7


async def test_create_agent_empty_json() -> None:
    """빈 JSON 객체는 유효하다."""
    # given
    agent_spec = "claude"
    sdk_options_json = "{}"
    binary_path = None
    opencode_url = None

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, ClaudeAgent)
    assert agent._sdk_options == {}


async def test_run_agent_and_execute_conflict() -> None:
    """--agent와 --execute를 동시에 사용할 수 없다."""
    # given/when/then
    with pytest.raises(typer.BadParameter, match="Cannot use --agent with --execute or --verify"):
        run(agent="claude", execute="droid")


async def test_run_agent_and_verify_conflict() -> None:
    """--agent와 --verify를 동시에 사용할 수 없다."""
    # given/when/then
    with pytest.raises(typer.BadParameter, match="Cannot use --agent with --execute or --verify"):
        run(agent="claude", verify="droid")


async def test_run_defaults_to_claude() -> None:
    """아무 에이전트도 지정하지 않으면 claude가 기본값."""
    # given/when/then
    # run() 함수는 anyio.run()을 호출하므로 mock 처리 필요
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock 설정
                    mock_agent = MagicMock(spec=Agent)
                    mock_create_agent.return_value = mock_agent
                    mock_ui = MagicMock()
                    mock_create_ui.return_value = mock_ui
                    mock_store = MagicMock()
                    mock_session_store.return_value = mock_store

                    # when
                    run(
                        agent=None,
                        execute=None,
                        verify=None,
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=None,
                        execute_binary=None,
                        verify_binary=None,
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url=None,
                        no_tui=False,
                        log=None,
                    )

                    # then
                    # create_agent가 "claude"로 호출되었는지 확인
                    assert mock_create_agent.call_count >= 1
                    first_call = mock_create_agent.call_args_list[0]
                    assert first_call[0][0] == "claude"


async def test_run_execute_without_verify() -> None:
    """--execute만 사용 (verify 없음)."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock 설정
                    mock_agent = MagicMock(spec=Agent)
                    mock_create_agent.return_value = mock_agent
                    mock_ui = MagicMock()
                    mock_create_ui.return_value = mock_ui
                    mock_store = MagicMock()
                    mock_session_store.return_value = mock_store

                    # when
                    run(
                        agent=None,
                        execute="droid:gpt-5",
                        verify=None,
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=None,
                        execute_binary=None,
                        verify_binary=None,
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url=None,
                        no_tui=False,
                        log=None,
                    )

                    # then
                    # create_agent가 execute에 대해 1번, verify에 대해 0번 호출
                    assert mock_create_agent.call_count == 1
                    first_call = mock_create_agent.call_args_list[0]
                    assert first_call[0][0] == "droid:gpt-5"


async def test_run_execute_and_verify() -> None:
    """--execute와 --verify 모두 사용."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock 설정
                    mock_agent = MagicMock(spec=Agent)
                    mock_create_agent.return_value = mock_agent
                    mock_ui = MagicMock()
                    mock_create_ui.return_value = mock_ui
                    mock_store = MagicMock()
                    mock_session_store.return_value = mock_store

                    # when
                    run(
                        agent=None,
                        execute="claude:sonnet",
                        verify="droid:gpt-5",
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=None,
                        execute_binary=None,
                        verify_binary=None,
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url=None,
                        no_tui=False,
                        log=None,
                    )

                    # then
                    # create_agent가 execute와 verify에 대해 각각 1번씩 호출
                    assert mock_create_agent.call_count == 2
                    first_call = mock_create_agent.call_args_list[0]
                    second_call = mock_create_agent.call_args_list[1]
                    assert first_call[0][0] == "claude:sonnet"
                    assert second_call[0][0] == "droid:gpt-5"


async def test_run_binary_resolution() -> None:
    """바이너리 resolve 우선순위 테스트."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock 설정
                    mock_agent = MagicMock(spec=Agent)
                    mock_create_agent.return_value = mock_agent
                    mock_ui = MagicMock()
                    mock_create_ui.return_value = mock_ui
                    mock_store = MagicMock()
                    mock_session_store.return_value = mock_store

                    # when
                    run(
                        agent=None,
                        execute="droid",
                        verify="droid",
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=Path("/common/droid"),
                        execute_binary=Path("/specific/execute-droid"),
                        verify_binary=Path("/specific/verify-droid"),
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url=None,
                        no_tui=False,
                        log=None,
                    )

                    # then
                    # create_agent 호출 시 resolve된 바이너리가 전달되는지 확인
                    assert mock_create_agent.call_count == 2
                    first_call = mock_create_agent.call_args_list[0]
                    second_call = mock_create_agent.call_args_list[1]

                    # execute는 execute_binary 사용
                    assert first_call[0][2] == Path("/specific/execute-droid")
                    # verify는 verify_binary 사용
                    assert second_call[0][2] == Path("/specific/verify-droid")


async def test_run_opencode_server_url_validation() -> None:
    """OpenCode 서버 URL 검증."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock 설정
                    mock_agent = MagicMock(spec=Agent)
                    mock_create_agent.return_value = mock_agent
                    mock_ui = MagicMock()
                    mock_create_ui.return_value = mock_ui
                    mock_store = MagicMock()
                    mock_session_store.return_value = mock_store

                    # when
                    run(
                        agent=None,
                        execute="opencode",
                        verify=None,
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=None,
                        execute_binary=None,
                        verify_binary=None,
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url="http://localhost:8080",
                        no_tui=False,
                        log=None,
                    )

                    # then
                    # create_agent가 검증된 URL과 함께 호출되는지 확인
                    assert mock_create_agent.call_count == 1
                    first_call = mock_create_agent.call_args_list[0]
                    assert first_call[0][3] == "http://localhost:8080"


async def test_run_opencode_invalid_url() -> None:
    """OpenCode 잘못된 URL."""
    # given/when/then
    with pytest.raises(typer.BadParameter, match="Invalid URL"):
        run(
            agent=None,
            execute="opencode",
            verify=None,
            execute_prompt="prompts/execute_command.md",
            verify_prompt="prompts/architect_command.md",
            execute_extra_prompt=None,
            verify_extra_prompt=None,
            binary=None,
            execute_binary=None,
            verify_binary=None,
            execute_sdk_options=None,
            verify_sdk_options=None,
            opencode_server_url="invalid-url",
            no_tui=False,
            log=None,
        )


async def test_run_ui_mode_cli() -> None:
    """--no-tui 플래그로 CLI 모드 선택."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock 설정
                    mock_agent = MagicMock(spec=Agent)
                    mock_create_agent.return_value = mock_agent
                    mock_ui = MagicMock()
                    mock_create_ui.return_value = mock_ui
                    mock_store = MagicMock()
                    mock_session_store.return_value = mock_store

                    # when
                    run(
                        agent=None,
                        execute=None,
                        verify=None,
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=None,
                        execute_binary=None,
                        verify_binary=None,
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url=None,
                        no_tui=True,
                        log=None,
                    )

                    # then
                    # create_ui가 "cli"로 호출되는지 확인
                    mock_create_ui.assert_called_once_with("cli")


async def test_run_ui_mode_tui() -> None:
    """기본값으로 TUI 모드 선택."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock 설정
                    mock_agent = MagicMock(spec=Agent)
                    mock_create_agent.return_value = mock_agent
                    mock_ui = MagicMock()
                    mock_create_ui.return_value = mock_ui
                    mock_store = MagicMock()
                    mock_session_store.return_value = mock_store

                    # when
                    run(
                        agent=None,
                        execute=None,
                        verify=None,
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=None,
                        execute_binary=None,
                        verify_binary=None,
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url=None,
                        no_tui=False,
                        log=None,
                    )

                    # then
                    # create_ui가 "tui"로 호출되는지 확인
                    mock_create_ui.assert_called_once_with("tui")


async def test_run_verify_only_uses_claude_for_both() -> None:
    """verify만 지정하면 agent가 claude로 설정되어 execute/verify 모두 claude를 사용한다."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock 설정
                    mock_agent = MagicMock(spec=Agent)
                    mock_create_agent.return_value = mock_agent
                    mock_ui = MagicMock()
                    mock_create_ui.return_value = mock_ui
                    mock_store = MagicMock()
                    mock_session_store.return_value = mock_store

                    # when
                    run(
                        agent=None,
                        execute=None,
                        verify="droid",
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=None,
                        execute_binary=None,
                        verify_binary=None,
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url=None,
                        no_tui=False,
                        log=None,
                    )

                    # then
                    assert mock_create_agent.call_count == 2
                    first_call = mock_create_agent.call_args_list[0]
                    second_call = mock_create_agent.call_args_list[1]
                    assert first_call[0][0] == "claude"
                    assert second_call[0][0] == "claude"
