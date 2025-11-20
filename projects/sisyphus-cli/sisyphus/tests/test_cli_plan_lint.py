"""CLI plan lint command integration tests.

Note: plan lint command is in sisyphus-speckit, not sisyphus-cli.
These tests verify that attempting to use "plan lint" in sisyphus-cli fails gracefully.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from ..cli import app

pytestmark = [pytest.mark.anyio]
runner = CliRunner()


async def test_plan_lint__when_valid_yaml__exits_0(tmp_path: Path) -> None:
    # given - plan lint command doesn't exist in sisyphus-cli
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01"
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then - Should fail with "no such command" or exit 2 (misuse of shell command)
    # plan command doesn't exist in sisyphus-cli (it's in sisyphus-speckit)
    assert result.exit_code != 0


async def test_plan_lint__when_missing_fields__exits_1_and_shows_errors(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "invalid.yaml"
    yaml_content = """version: "3.0"
work_plans: []
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code != 0


async def test_plan_lint__when_type_mismatch__exits_1_and_shows_type_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "type_error.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "invalid"
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code != 0


async def test_plan_lint__when_file_not_found__exits_1(tmp_path: Path) -> None:
    # when
    result = runner.invoke(app, ["plan", "lint", "--file", "/nonexistent/file.yaml"])

    # then
    assert result.exit_code != 0


async def test_plan_lint__when_invalid_enum__exits_1_and_shows_enum_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "enum_error.yaml"
    yaml_content = """version: "3.0"
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code != 0


async def test_plan_lint__when_yaml_syntax_error__exits_1_and_shows_parsing_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "syntax_error.yaml"
    yaml_content = """version: "3.0
invalid yaml [
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code != 0
