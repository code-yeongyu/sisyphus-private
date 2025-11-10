#!/usr/bin/env python3
"""Migrate sessions.json from legacy {agent: {session}} to {agent: {plan_id: {session}}} structure

This script detects and converts legacy sessions.json files created before commit e8fc7e5
to the new multi-plan session structure.

Legacy structure:
{
  "claude": {
    "session_id": "...",
    "updated": "..."
  }
}

Target structure:
{
  "claude": {
    "default": {
      "session_id": "...",
      "updated": "..."
    }
  }
}
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def detect_legacy_structure(data: dict[str, Any]) -> bool:
    """Detect if sessions.json uses legacy structure.

    Legacy structure has session_id directly under agent type,
    not nested under plan_id.

    Args:
        data: Parsed sessions.json data

    Returns:
        True if legacy structure detected, False otherwise
    """
    if not data:
        return False

    for agent_type, agent_data in data.items():
        if not isinstance(agent_data, dict):
            continue

        # Legacy: session_id exists directly under agent
        if "session_id" in agent_data:
            return True

        # New: session_id exists under plan_id (nested one level deeper)
        # If any value has session_id, it's new structure
        for plan_data in agent_data.values():
            if isinstance(plan_data, dict) and "session_id" in plan_data:
                return False

    return False


def migrate_sessions(data: dict[str, Any]) -> dict[str, Any]:
    """Convert legacy structure to new multi-plan structure.

    Wraps session data in "default" plan_id.

    Args:
        data: Legacy sessions data

    Returns:
        Migrated sessions data
    """
    migrated = {}

    for agent_type, agent_data in data.items():
        if not isinstance(agent_data, dict):
            migrated[agent_type] = agent_data
            continue

        # Check if this agent has legacy structure
        if "session_id" in agent_data:
            # Legacy structure: wrap in "default" plan_id
            migrated[agent_type] = {
                "default": {
                    "session_id": agent_data.get("session_id", ""),
                    "updated": agent_data.get("updated", datetime.now(UTC).isoformat()),
                }
            }
        else:
            # Already new structure or empty
            migrated[agent_type] = agent_data

    return migrated


def main() -> None:
    """CLI entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate sessions.json to multi-plan structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "sessions_file",
        type=Path,
        help="Path to sessions.json file to migrate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )

    args = parser.parse_args()
    sessions_file: Path = args.sessions_file

    # Validate input file
    if not sessions_file.exists():
        print(f"❌ Error: File not found: {sessions_file}")
        raise SystemExit(1)

    if not sessions_file.is_file():
        print(f"❌ Error: Not a file: {sessions_file}")
        raise SystemExit(1)

    # Load sessions.json
    try:
        content = sessions_file.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {sessions_file}: {e}")
        raise SystemExit(1)
    except OSError as e:
        print(f"❌ Error: Cannot read {sessions_file}: {e}")
        raise SystemExit(1)

    # Check if migration needed
    is_legacy = detect_legacy_structure(data)

    if not is_legacy:
        print(f"✅ {sessions_file} already uses new structure - no migration needed")
        print("\nCurrent structure:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    # Migrate data
    migrated = migrate_sessions(data)

    print(f"🔄 Legacy structure detected in {sessions_file}")
    print("\n📋 Migration summary:")
    print(f"   Original structure: {len(data)} agent(s)")
    print(f"   Migrated structure: {len(migrated)} agent(s)")

    print("\n📝 Changes:")
    for agent_type in data:
        if agent_type in migrated:
            print(f"   - {agent_type}: session wrapped in 'default' plan_id")

    if args.dry_run:
        print("\n🔍 Dry run mode - no files modified")
        print("\nMigrated structure preview:")
        print(json.dumps(migrated, indent=2, ensure_ascii=False))
        return

    # Create backup
    backup_file = sessions_file.with_suffix(sessions_file.suffix + ".pre-migration")
    try:
        shutil.copy2(sessions_file, backup_file)
        print(f"\n💾 Backup created: {backup_file}")
    except OSError as e:
        print(f"❌ Error: Cannot create backup: {e}")
        raise SystemExit(1)

    # Write migrated data
    try:
        migrated_content = json.dumps(migrated, indent=2, ensure_ascii=False) + "\n"
        sessions_file.write_text(migrated_content, encoding="utf-8")
        print(f"✅ Migration completed: {sessions_file}")
    except OSError as e:
        print(f"❌ Error: Cannot write migrated file: {e}")
        print(f"   Original file preserved, backup at: {backup_file}")
        raise SystemExit(1)

    print("\n📊 Final structure:")
    print(json.dumps(migrated, indent=2, ensure_ascii=False))

    print("\n✨ Migration successful!")
    print(f"   Original backup: {backup_file}")
    print(f"   Migrated file:   {sessions_file}")


if __name__ == "__main__":
    main()
