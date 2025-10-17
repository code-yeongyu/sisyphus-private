"""CLI integration tests for sisyphus/cli.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest
import typer

from sisyphus.agents.base import Agent
from sisyphus.agents.claude import ClaudeAgent
from sisyphus.agents.opencode import OpenCodeAgent
from sisyphus.cli import create_agent, resolve_binary, run, validate_url

pytestmark = [pytest.mark.anyio()]


async def test_validate_url_valid_http() -> None:
    """Validates a valid HTTP URL."""
    # given
    url = "http://localhost:8080"

    # when
    result = validate_url(url)

    # then
    assert result == url


async def test_validate_url_valid_https() -> None:
    """Validates a valid HTTPS URL."""
    # given
    url = "https://example.com:3000/api"

    # when
    result = validate_url(url)

    # then
    assert result == url


async def test_validate_url_invalid_no_scheme() -> None:
    """Invalid URL without scheme."""
    # given
    url = "localhost:8080"

    # when/then
    with pytest.raises(typer.BadParameter, match="Invalid URL"):
        validate_url(url)


async def test_validate_url_invalid_no_netloc() -> None:
    """Invalid URL without netloc."""
    # given
    url = "http://"

    # when/then
    with pytest.raises(typer.BadParameter, match="Invalid URL"):
        validate_url(url)


async def test_resolve_binary_specific_priority() -> None:
    """Specific binary takes priority."""
    # given
    common = Path("/common/binary")
    specific = Path("/specific/binary")

    # when
    result = resolve_binary(common, specific)

    # then
    assert result == specific


async def test_resolve_binary_common_fallback() -> None:
    """Falls back to common if specific is None."""
    # given
    common = Path("/common/binary")
    specific = None

    # when
    result = resolve_binary(common, specific)

    # then
    assert result == common


async def test_resolve_binary_both_none() -> None:
    """Returns None if both are None."""
    # given
    common = None
    specific = None

    # when
    result = resolve_binary(common, specific)

    # then
    assert result is None


async def test_create_agent_claude_without_model() -> None:
    """Creates Claude agent without model."""
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
    """Creates Claude agent with model."""
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
    """Creates Claude agent with SDK options."""
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


async def test_create_agent_opencode() -> None:
    """Creates OpenCode agent."""
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
    """Unknown agent type."""
    # given
    agent_spec = "unknown-agent"
    sdk_options_json = None
    binary_path = None
    opencode_url = None

    # when/then
    with pytest.raises(typer.BadParameter, match="Unknown agent type"):
        create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)


async def test_create_agent_invalid_json() -> None:
    """Invalid JSON SDK options."""
    # given
    agent_spec = "claude"
    sdk_options_json = '{"invalid": json}'
    binary_path = None
    opencode_url = None

    # when/then
    with pytest.raises(typer.BadParameter, match="Invalid JSON in SDK options"):
        create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)


async def test_create_agent_json_with_model_override() -> None:
    """Overrides model with agent_spec when SDK options JSON contains model."""
    # given
    agent_spec = "claude:sonnet-4"
    sdk_options_json = '{"model": "old-model", "temperature": 0.7}'
    binary_path = None
    opencode_url = None

    # when
    agent = create_agent(agent_spec, sdk_options_json, binary_path, opencode_url)

    # then
    assert isinstance(agent, ClaudeAgent)
    # agent_spec's model is added to sdk_options
    assert agent._sdk_options["model"] == "sonnet-4"
    assert agent._sdk_options["temperature"] == 0.7


async def test_create_agent_empty_json() -> None:
    """Empty JSON object is valid."""
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
    """Cannot use --agent with --execute simultaneously."""
    # given/when/then
    with pytest.raises(typer.BadParameter, match="Cannot use --agent with --execute or --verify"):
        run(agent="claude", execute="opencode")


async def test_run_agent_and_verify_conflict() -> None:
    """Cannot use --agent with --verify simultaneously."""
    # given/when/then
    with pytest.raises(typer.BadParameter, match="Cannot use --agent with --execute or --verify"):
        run(agent="claude", verify="opencode")


async def test_run_defaults_to_claude() -> None:
    """Defaults to claude when no agent is specified."""
    # given/when/then
    # run() calls anyio.run() so mock handling is required
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock setup
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
                    # Verify create_agent was called with "claude"
                    assert mock_create_agent.call_count >= 1
                    first_call = mock_create_agent.call_args_list[0]
                    assert first_call[0][0] == "claude"


async def test_run_execute_without_verify() -> None:
    """Uses only --execute (no verify)."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock setup
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
                        opencode_server_url=None,
                        no_tui=False,
                        log=None,
                    )

                    # then
                    # create_agent is called for both execute and verify (verify uses same as execute)
                    assert mock_create_agent.call_count == 2
                    first_call = mock_create_agent.call_args_list[0]
                    assert first_call[0][0] == "opencode"


async def test_run_execute_and_verify() -> None:
    """Uses both --execute and --verify."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock setup
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
                        verify="opencode",
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
                    # create_agent is called once each for execute and verify
                    assert mock_create_agent.call_count == 2
                    first_call = mock_create_agent.call_args_list[0]
                    second_call = mock_create_agent.call_args_list[1]
                    assert first_call[0][0] == "claude:sonnet"
                    assert second_call[0][0] == "opencode"


async def test_run_binary_resolution() -> None:
    """Tests binary resolution priority."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock setup
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
                        verify="opencode",
                        execute_prompt="prompts/execute_command.md",
                        verify_prompt="prompts/architect_command.md",
                        execute_extra_prompt=None,
                        verify_extra_prompt=None,
                        binary=Path("/common/opencode"),
                        execute_binary=Path("/specific/execute-opencode"),
                        verify_binary=Path("/specific/verify-opencode"),
                        execute_sdk_options=None,
                        verify_sdk_options=None,
                        opencode_server_url=None,
                        no_tui=False,
                        log=None,
                    )

                    # then
                    # Verify resolved binaries are passed to create_agent
                    assert mock_create_agent.call_count == 2
                    first_call = mock_create_agent.call_args_list[0]
                    second_call = mock_create_agent.call_args_list[1]

                    # execute uses execute_binary
                    assert first_call[0][2] == Path("/specific/execute-opencode")
                    # verify uses verify_binary
                    assert second_call[0][2] == Path("/specific/verify-opencode")


async def test_run_opencode_server_url_validation() -> None:
    """Validates OpenCode server URL."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock setup
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
                    # create_agent is called for both execute and verify
                    assert mock_create_agent.call_count == 2
                    first_call = mock_create_agent.call_args_list[0]
                    assert first_call[0][3] == "http://localhost:8080"


async def test_run_opencode_invalid_url() -> None:
    """OpenCode invalid URL."""
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
    """Selects CLI mode with --no-tui flag."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock setup
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
                    # Verify create_ui is called with "cli" (theme=None for CLI mode)
                    mock_create_ui.assert_called_once_with("cli", theme=None)


async def test_run_ui_mode_tui() -> None:
    """Selects TUI mode by default."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock setup
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
                    mock_create_ui.assert_called_once_with("tui", theme=ANY)


async def test_run_verify_only_uses_claude_for_both() -> None:
    """When only verify is specified, agent is set to claude so both execute/verify use claude."""
    # given/when/then
    with patch("sisyphus.cli.create_agent") as mock_create_agent:
        with patch("sisyphus.cli.create_ui") as mock_create_ui:
            with patch("sisyphus.cli.SessionStore") as mock_session_store:
                with patch("sisyphus.cli.anyio.run"):
                    # Mock setup
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
                        verify="opencode",
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
