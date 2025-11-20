"""CLI integration tests for sisyphus/cli.py."""

from __future__ import annotations


import pytest

from sisyphus_core.agents.base import Agent
from sisyphus_core.agents.claude import ClaudeAgent
from sisyphus_core.agents.opencode import OpenCodeAgent
from ..cli.work import run
from sisyphus_core.utils.cli_helpers import create_agent, resolve_binary, validate_url

pytestmark = [pytest.mark.anyio()]
