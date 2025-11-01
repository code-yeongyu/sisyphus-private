from __future__ import annotations

from pathlib import Path


def resolve_cwd(cwd: str | None) -> Path:
    if cwd is None:
        return Path.cwd()
    return Path(cwd).resolve()
