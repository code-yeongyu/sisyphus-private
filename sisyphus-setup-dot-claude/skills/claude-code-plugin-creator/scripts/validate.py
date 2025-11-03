#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


def validate_plugin(plugin_path: Path) -> bool:
    errors = []

    manifest_path = plugin_path / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        errors.append(f"Missing plugin manifest: {manifest_path}")
        return False

    try:
        with open(manifest_path) as file:
            manifest = json.load(file)

        if "name" not in manifest:
            errors.append("plugin.json must have 'name' field")

        if "name" in manifest and " " in manifest["name"]:
            errors.append(f"Plugin name cannot contain spaces: {manifest['name']}")

    except json.JSONDecodeError as error:
        errors.append(f"Invalid JSON in plugin.json: {error}")

    if errors:
        print("❌ Plugin validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False

    print(f"✅ Plugin validation passed: {plugin_path.name}")
    return True


def validate_marketplace(marketplace_path: Path) -> bool:
    errors = []

    manifest_path = marketplace_path / ".claude-plugin" / "marketplace.json"
    if not manifest_path.exists():
        errors.append(f"Missing marketplace manifest: {manifest_path}")
        return False

    try:
        with open(manifest_path) as file:
            manifest = json.load(file)

        if "name" not in manifest:
            errors.append("marketplace.json must have 'name' field")

        if "owner" not in manifest:
            errors.append("marketplace.json must have 'owner' field")

        if "plugins" not in manifest:
            errors.append("marketplace.json must have 'plugins' array")

    except json.JSONDecodeError as error:
        errors.append(f"Invalid JSON in marketplace.json: {error}")

    if errors:
        print("❌ Marketplace validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False

    print(f"✅ Marketplace validation passed: {marketplace_path.name}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Claude Code plugin or marketplace")
    parser.add_argument("path", type=Path, help="Path to plugin or marketplace directory")
    parser.add_argument(
        "--type",
        choices=["plugin", "marketplace", "auto"],
        default="auto",
        help="Type to validate (default: auto-detect)",
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"❌ Error: Path does not exist: {args.path}")
        sys.exit(1)

    if not args.path.is_dir():
        print(f"❌ Error: Path is not a directory: {args.path}")
        sys.exit(1)

    claude_plugin_dir = args.path / ".claude-plugin"
    if not claude_plugin_dir.exists():
        print("❌ Error: Not a valid plugin or marketplace (missing .claude-plugin/ directory)")
        sys.exit(1)

    validation_type = args.type
    if validation_type == "auto":
        if (claude_plugin_dir / "plugin.json").exists():
            validation_type = "plugin"
        elif (claude_plugin_dir / "marketplace.json").exists():
            validation_type = "marketplace"
        else:
            print("❌ Error: Cannot auto-detect type (no plugin.json or marketplace.json found)")
            sys.exit(1)

    if validation_type == "plugin":
        success = validate_plugin(args.path)
    else:
        success = validate_marketplace(args.path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
