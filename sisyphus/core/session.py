from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import anyio


class SessionStore:
    """세션 영속성 관리 (파일 락 포함)"""

    def __init__(self, base_dir: Path = Path("./sessions")) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(exist_ok=True, parents=True)
        self.sessions_file = self.base_dir / "sessions.json"
        self.backup_file = self.base_dir / "sessions.json.bak"
        self.lock = anyio.Lock()

    def _load_sessions_sync(self) -> dict[str, dict[str, Any]]:
        """Load sessions from file with corruption recovery (synchronous)"""
        # Try main file first
        if self.sessions_file.exists():
            try:
                content = self.sessions_file.read_text(encoding="utf-8")
                return json.loads(content)  # type: ignore[no-any-return]
            except (json.JSONDecodeError, OSError):
                # Main file corrupted, try backup
                pass

        # Try backup file
        if self.backup_file.exists():
            try:
                content = self.backup_file.read_text(encoding="utf-8")
                return json.loads(content)  # type: ignore[no-any-return]
            except (json.JSONDecodeError, OSError):
                pass

        # Both failed, start fresh
        return {}

    async def _save_sessions_atomic(self, sessions: dict[str, dict[str, Any]]) -> None:
        """원자적 저장 (임시 파일 + rename)"""
        # Create backup of existing file before writing
        if self.sessions_file.exists():
            # Remove old backup if exists
            if self.backup_file.exists():
                await anyio.to_thread.run_sync(self.backup_file.unlink)
            # Rename current file to backup
            await anyio.to_thread.run_sync(self.sessions_file.rename, self.backup_file)

        # Write to temporary file
        temp_file = self.base_dir / f"sessions.json.tmp.{uuid.uuid4().hex}"
        try:
            async with await anyio.open_file(temp_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(sessions, indent=2, ensure_ascii=False))
                await f.flush()

            # Atomic rename
            await anyio.to_thread.run_sync(temp_file.rename, self.sessions_file)
        except Exception:
            # Clean up temp file on failure
            if temp_file.exists():
                await anyio.to_thread.run_sync(temp_file.unlink)
            raise

    async def get_session(self, agent_type: str) -> str | None:
        """Get session ID for specific agent"""
        async with self.lock:
            sessions = await anyio.to_thread.run_sync(self._load_sessions_sync)
            agent_data = sessions.get(agent_type)
            if agent_data is None:
                return None
            return agent_data.get("session_id")  # type: ignore[no-any-return]

    async def save_session(self, agent_type: str, session_id: str) -> None:
        """Save session ID for specific agent"""
        async with self.lock:
            sessions = await anyio.to_thread.run_sync(self._load_sessions_sync)
            sessions[agent_type] = {
                "session_id": session_id,
                "updated": datetime.now(UTC).isoformat(),
            }
            await self._save_sessions_atomic(sessions)

    async def delete_session(self, agent_type: str) -> None:
        """Delete session for specific agent"""
        async with self.lock:
            sessions = await anyio.to_thread.run_sync(self._load_sessions_sync)
            if agent_type in sessions:
                del sessions[agent_type]
                await self._save_sessions_atomic(sessions)

    async def list_sessions(self) -> dict[str, dict[str, Any]]:
        """List all sessions"""
        async with self.lock:
            return await anyio.to_thread.run_sync(self._load_sessions_sync)
