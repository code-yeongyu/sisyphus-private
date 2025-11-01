from __future__ import annotations

import json
import shutil
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
