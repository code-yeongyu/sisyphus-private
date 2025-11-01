from __future__ import annotations

import json
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

        self.status_path.parent.mkdir(parents=True, exist_ok=True)

        async with await anyio.open_file(self.status_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(status.model_dump(), indent=2, ensure_ascii=False))
