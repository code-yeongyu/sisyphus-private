"""Tests for sisyphus.utils.types module."""

from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus.utils.types import AgentConfig, AgentMessage

pytestmark = [pytest.mark.anyio()]


async def test_agent_message_creation() -> None:
    # given
    role = "user"
    content = "Hello, world!"

    # when
    message = AgentMessage(role=role, content=content)

    # then
    assert message.role == role
    assert message.content == content
    assert message.metadata == {}


async def test_agent_message_with_metadata() -> None:
    # given
    role = "assistant"
    content = "Response text"
    metadata = {"timestamp": "2025-10-09", "model": "claude-sonnet-4"}

    # when
    message = AgentMessage(role=role, content=content, metadata=metadata)

    # then
    assert message.role == role
    assert message.content == content
    assert message.metadata == metadata
    assert message.metadata["timestamp"] == "2025-10-09"
    assert message.metadata["model"] == "claude-sonnet-4"


async def test_agent_message_metadata_default_factory() -> None:
    # given
    message1 = AgentMessage(role="user", content="First")
    message2 = AgentMessage(role="user", content="Second")

    # when
    message1.metadata["key"] = "value1"
    message2.metadata["key"] = "value2"

    # then
    assert message1.metadata["key"] == "value1"
    assert message2.metadata["key"] == "value2"
    assert message1.metadata is not message2.metadata


async def test_agent_config_creation() -> None:
    # given
    agent_type = "claude"
    model = "claude-sonnet-4-5-20250929"
    base_prompt = "/execute"
    extra_prompt = "Extra instructions"
    binary = Path("/usr/local/bin/claude")
    sdk_options = {"permission_mode": "bypassPermissions"}

    # when
    config = AgentConfig(
        agent_type=agent_type,
        model=model,
        prompt=(base_prompt, extra_prompt),
        binary=binary,
        sdk_options=sdk_options,
    )

    # then
    assert config.agent_type == agent_type
    assert config.model == model
    assert config.prompt == (base_prompt, extra_prompt)
    assert config.prompt[0] == base_prompt
    assert config.prompt[1] == extra_prompt
    assert config.binary == binary
    assert config.sdk_options == sdk_options
    assert config.opencode_server_url is None


async def test_agent_config_with_none_values() -> None:
    # given
    agent_type = "opencode"
    base_prompt = "plain-text-prompt"

    # when
    config = AgentConfig(
        agent_type=agent_type,
        model=None,
        prompt=(base_prompt, None),
        binary=None,
        sdk_options={},
    )

    # then
    assert config.agent_type == agent_type
    assert config.model is None
    assert config.prompt == (base_prompt, None)
    assert config.prompt[0] == base_prompt
    assert config.prompt[1] is None
    assert config.binary is None
    assert config.sdk_options == {}
    assert config.opencode_server_url is None


async def test_agent_config_with_opencode_server_url() -> None:
    # given
    agent_type = "opencode"
    server_url = "http://localhost:8080"

    # when
    config = AgentConfig(
        agent_type=agent_type,
        model=None,
        prompt=("prompt", None),
        binary=None,
        sdk_options={},
        opencode_server_url=server_url,
    )

    # then
    assert config.agent_type == agent_type
    assert config.opencode_server_url == server_url


async def test_agent_config_sdk_options_default_factory() -> None:
    # given
    config1 = AgentConfig(
        agent_type="claude",
        model=None,
        prompt=("prompt", None),
        binary=None,
    )
    config2 = AgentConfig(
        agent_type="opencode",
        model=None,
        prompt=("prompt", None),
        binary=None,
    )

    # when
    config1.sdk_options["key"] = "value1"
    config2.sdk_options["key"] = "value2"

    # then
    assert config1.sdk_options["key"] == "value1"
    assert config2.sdk_options["key"] == "value2"
    assert config1.sdk_options is not config2.sdk_options
