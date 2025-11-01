from __future__ import annotations

import json
import shutil
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import anyio
from pydantic import BaseModel


class CurrentPlan(BaseModel):
    plan_path: str
    plan_root: str
    updated_at: str


class StatusFile(BaseModel):
    version: int = 1
    current_plan: CurrentPlan | None = None


class StatusManager:
    # Worktree cache (class-level)
    _worktree_cache: dict[Path, list[Path]] | None = None
    _cache_timestamp: float | None = None
    CACHE_TTL = 60.0  # 60초

    def __init__(self, status_path: Path) -> None:
        self.status_path = status_path
        self.backup_path = status_path.parent / f"{status_path.name}.bak"
        self.lock = anyio.Lock()

    def _remove_path_sync(self, path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    async def get(self) -> StatusFile:
        if not self.status_path.exists():
            return StatusFile(version=1, current_plan=None)

        async with await anyio.open_file(self.status_path, "r", encoding="utf-8") as f:
            content = await f.read()

        data = json.loads(content)
        return StatusFile(**data)

    async def set_current(self, plan_path: str, plan_root: str) -> None:
        now = datetime.now(UTC).isoformat()

        status = StatusFile(
            version=1,
            current_plan=CurrentPlan(
                plan_path=plan_path,
                plan_root=plan_root,
                updated_at=now,
            ),
        )

        async with self.lock:
            self.status_path.parent.mkdir(parents=True, exist_ok=True)

            if self.status_path.exists():
                if self.backup_path.exists():
                    await anyio.to_thread.run_sync(self._remove_path_sync, self.backup_path)
                await anyio.to_thread.run_sync(self.status_path.rename, self.backup_path)

            temp_file = self.status_path.parent / f"{self.status_path.name}.tmp.{uuid.uuid4().hex}"
            try:
                async with await anyio.open_file(temp_file, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(status.model_dump(), indent=2, ensure_ascii=False))
                    await f.flush()

                await anyio.to_thread.run_sync(temp_file.rename, self.status_path)
            except Exception:
                if temp_file.exists():
                    await anyio.to_thread.run_sync(temp_file.unlink)
                raise

    @classmethod
    def _is_cache_expired(cls) -> bool:
        if cls._cache_timestamp is None:
            return True
        return time.time() - cls._cache_timestamp > cls.CACHE_TTL

    @classmethod
    async def _refresh_worktree_cache(cls) -> None:
        result = await anyio.run_process(
            ["git", "worktree", "list", "--porcelain"],
            check=False,
        )

        if result.returncode != 0:
            cls._worktree_cache = {}
            cls._cache_timestamp = time.time()
            return

        output = result.stdout.decode("utf-8")
        worktrees: dict[Path, list[Path]] = {}
        current_worktree: Path | None = None

        for line in output.strip().split("\n"):
            if not line:
                continue
            if line.startswith("worktree "):
                current_worktree = Path(line.split(" ", 1)[1])
                worktrees[current_worktree] = []
            elif line.startswith("branch ") and current_worktree:
                worktrees[current_worktree].append(Path(line.split(" ", 1)[1]))

        cls._worktree_cache = worktrees
        cls._cache_timestamp = time.time()

    @classmethod
    async def detect_worktree(cls) -> Path:
        if cls._is_cache_expired():
            await cls._refresh_worktree_cache()

        result = await anyio.run_process(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
        )

        if result.returncode != 0:
            return Path.cwd()

        return Path(result.stdout.decode("utf-8").strip())

    @classmethod
    async def list_all(cls) -> list[Path]:
        if cls._is_cache_expired():
            await cls._refresh_worktree_cache()

        if cls._worktree_cache is None:
            return []

        return list(cls._worktree_cache.keys())
