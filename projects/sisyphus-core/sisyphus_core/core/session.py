from __future__ import annotations

import json
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import anyio


class SessionStore:
    """Manage session persistence with file locking

    Sessions are stored in .sisyphus/sessions/ directory in the current working directory.

    Structure: {agent_type: {plan_id: {session_id, updated}}}
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize SessionStore with cwd-based session directory.

        Args:
            base_dir: Optional base directory for sessions.
                     If None, uses .sisyphus/sessions/ in current working directory.
        """
        if base_dir is None:
            base_dir = Path.cwd() / ".sisyphus" / "sessions"

        self.base_dir = base_dir
        self.base_dir.mkdir(exist_ok=True, parents=True)
        self.sessions_file = self.base_dir / "sessions.json"
        self.backup_file = self.base_dir / "sessions.json.bak"
        self.lock = anyio.Lock()

    def _remove_path_sync(self, path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def _load_sessions_sync(self) -> dict[str, dict[str, Any]]:
        """Load sessions from file with corruption recovery (synchronous)"""
        if self.sessions_file.exists():
            try:
                content = self.sessions_file.read_text(encoding="utf-8")
                return json.loads(content)  # type: ignore[no-any-return]
            except (json.JSONDecodeError, OSError):
                pass

        if self.backup_file.exists():
            try:
                content = self.backup_file.read_text(encoding="utf-8")
                return json.loads(content)  # type: ignore[no-any-return]
            except (json.JSONDecodeError, OSError):
                pass

        return {}

    async def _save_sessions_atomic(self, sessions: dict[str, dict[str, Any]]) -> None:
        """Atomic save using temporary file and rename"""
        if self.sessions_file.exists():
            if self.backup_file.exists():
                await anyio.to_thread.run_sync(self._remove_path_sync, self.backup_file)
            await anyio.to_thread.run_sync(self.sessions_file.rename, self.backup_file)

        temp_file = self.base_dir / f"sessions.json.tmp.{uuid.uuid4().hex}"
        try:
            async with await anyio.open_file(temp_file, "w", encoding="utf-8") as f:
                _ = await f.write(json.dumps(sessions, indent=2, ensure_ascii=False))
                await f.flush()

            await anyio.to_thread.run_sync(temp_file.rename, self.sessions_file)
        except Exception:
            if temp_file.exists():
                await anyio.to_thread.run_sync(temp_file.unlink)
            raise

    async def get_session(self, agent_type: str, plan_id: str) -> str | None:
        """Get session ID for specific agent and plan

        Args:
            agent_type: Type of agent (claude, opencode, etc.)
            plan_id: Plan ID

        Returns:
            Session ID if found, None otherwise
        """
        async with self.lock:
            sessions = await anyio.to_thread.run_sync(self._load_sessions_sync)
            agent_data = sessions.get(agent_type)
            if agent_data is None:
                return None

            plan_data = agent_data.get(plan_id)
            if plan_data is None:
                return None
            return plan_data.get("session_id")  # type: ignore[no-any-return]

    async def save_session(self, agent_type: str, session_id: str, plan_id: str) -> None:
        """Save session ID for specific agent and plan

        Args:
            agent_type: Type of agent (claude, opencode, etc.)
            session_id: Session ID to save
            plan_id: Plan ID
        """
        async with self.lock:
            sessions = await anyio.to_thread.run_sync(self._load_sessions_sync)

            if agent_type not in sessions:
                sessions[agent_type] = {}

            sessions[agent_type][plan_id] = {
                "session_id": session_id,
                "updated": datetime.now(UTC).isoformat(),
            }

            await self._save_sessions_atomic(sessions)

    async def delete_session(self, agent_type: str, plan_id: str | None = None) -> None:
        """Delete session for specific agent and plan

        Args:
            agent_type: Type of agent (claude, opencode, etc.)
            plan_id: Optional plan ID. If None, deletes all sessions for the agent
        """
        async with self.lock:
            sessions = await anyio.to_thread.run_sync(self._load_sessions_sync)
            if agent_type not in sessions:
                return

            if plan_id is None:
                del sessions[agent_type]
            else:
                agent_data = sessions[agent_type]
                if plan_id in agent_data:
                    del agent_data[plan_id]
                    if not agent_data:
                        del sessions[agent_type]

            await self._save_sessions_atomic(sessions)

    async def list_sessions(self) -> dict[str, dict[str, Any]]:
        """List all sessions"""
        async with self.lock:
            return await anyio.to_thread.run_sync(self._load_sessions_sync)
