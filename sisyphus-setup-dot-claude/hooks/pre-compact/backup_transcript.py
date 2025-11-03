#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.12"
# dependencies = []
# ///

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import TypedDict


class PreCompactInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str


def main() -> None:
    try:
        data: PreCompactInput = json.loads(sys.stdin.read())

        session_id = data.get("session_id", "")
        transcript_path = data.get("transcript_path", "")

        if not session_id or not transcript_path:
            sys.exit(0)

        backup_dir = Path.home() / ".claude" / "pre-compact-session-histories"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_filename = f"{session_id}-{timestamp}.jsonl"
        backup_path = backup_dir / backup_filename

        source_path = Path(transcript_path)
        if source_path.exists():
            shutil.copy(source_path, backup_path)

        sys.exit(0)

    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
