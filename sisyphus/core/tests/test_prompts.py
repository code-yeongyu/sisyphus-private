from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus.core.prompts import PromptResolver

pytestmark = [pytest.mark.anyio]


async def test_resolve_slash_command_success(tmp_path: Path) -> None:
    # given
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    execute_file = prompts_dir / "execute_command.md"
    execute_file.write_text("Execute prompt content", encoding="utf-8")
    resolver = PromptResolver(prompts_dir=prompts_dir)

    # when
    result = await resolver.resolve("/execute")

    # then
    assert result == "Execute prompt content"


async def test_resolve_slash_command_not_found(tmp_path: Path) -> None:
    # given
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    resolver = PromptResolver(prompts_dir=prompts_dir)

    # when/then
    with pytest.raises(FileNotFoundError) as exc_info:
        await resolver.resolve("/nonexistent")
    assert "Slash command file not found" in str(exc_info.value)


async def test_resolve_file_path_with_path_object(tmp_path: Path) -> None:
    # given
    test_file = tmp_path / "test_prompt.md"
    test_file.write_text("File prompt content", encoding="utf-8")
    resolver = PromptResolver()

    # when
    result = await resolver.resolve(test_file)

    # then
    assert result == "File prompt content"


async def test_resolve_file_path_with_string(tmp_path: Path) -> None:
    # given
    test_file = tmp_path / "test_prompt.md"
    test_file.write_text("String path content", encoding="utf-8")
    resolver = PromptResolver()

    # when
    result = await resolver.resolve(str(test_file))

    # then
    assert result == "String path content"


async def test_resolve_file_not_found() -> None:
    # given
    resolver = PromptResolver()
    nonexistent_path = "/nonexistent/path/to/file.md"

    # when
    result = await resolver.resolve(nonexistent_path)

    # then
    assert result == nonexistent_path


async def test_resolve_plain_text() -> None:
    # given
    resolver = PromptResolver()
    plain_text = "This is a plain text prompt"

    # when
    result = await resolver.resolve(plain_text)

    # then
    assert result == plain_text


async def test_resolve_slash_command_with_extra(tmp_path: Path) -> None:
    # given
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    architect_file = prompts_dir / "architect_command.md"
    architect_file.write_text("Architect prompt", encoding="utf-8")
    resolver = PromptResolver(prompts_dir=prompts_dir)
    extra = "Additional instructions"

    # when
    result = await resolver.resolve("/architect", extra=extra)

    # then
    assert result == "Architect prompt\n\nAdditional instructions"


async def test_resolve_file_path_with_extra(tmp_path: Path) -> None:
    # given
    test_file = tmp_path / "custom.md"
    test_file.write_text("Custom prompt", encoding="utf-8")
    resolver = PromptResolver()
    extra = "Extra context"

    # when
    result = await resolver.resolve(test_file, extra=extra)

    # then
    assert result == "Custom prompt\n\nExtra context"


async def test_resolve_plain_text_with_extra() -> None:
    # given
    resolver = PromptResolver()
    plain_text = "Base prompt"
    extra = "Extra prompt"

    # when
    result = await resolver.resolve(plain_text, extra=extra)

    # then
    assert result == "Base prompt\n\nExtra prompt"


async def test_resolve_with_none_extra(tmp_path: Path) -> None:
    # given
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    execute_file = prompts_dir / "execute_command.md"
    execute_file.write_text("Execute content", encoding="utf-8")
    resolver = PromptResolver(prompts_dir=prompts_dir)

    # when
    result = await resolver.resolve("/execute", extra=None)

    # then
    assert result == "Execute content"
