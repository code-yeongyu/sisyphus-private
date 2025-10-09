from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike


class PromptResolver:
    def __init__(self, prompts_dir: Path = Path("prompts")) -> None:
        self._prompts_dir = prompts_dir

    async def resolve(
        self,
        prompt: str | PathLike[str],
        extra: str | None = None,
    ) -> str:
        prompt_str = str(prompt) if not isinstance(prompt, str) else prompt

        if Path(prompt_str).exists():
            resolved_text = Path(prompt_str).read_text(encoding="utf-8")

        elif prompt_str.startswith("/") and "/" not in prompt_str[1:]:
            command_name = prompt_str[1:]
            command_file = self._prompts_dir / f"{command_name}_command.md"

            if not command_file.exists():
                msg = f"Slash command file not found: {command_file}"
                raise FileNotFoundError(msg)

            resolved_text = command_file.read_text(encoding="utf-8")

        else:
            resolved_text = prompt_str

        if extra is not None:
            resolved_text = f"{resolved_text}\n\n{extra}"

        return resolved_text
