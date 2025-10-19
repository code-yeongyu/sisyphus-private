#!/usr/bin/env python3
"""
Setup script for installing Sisyphus essential Claude Code plugin.

This script:
1. Copies hooks from .github/workflows/.claude/hooks/ to ~/.claude/hooks/
2. Installs the essentials plugin
3. Sets up necessary configuration
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup Sisyphus essential Claude Code plugin"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force overwrite existing files without prompting",
    )
    args = parser.parse_args()

    print("🚀 Setting up Sisyphus essential Claude Code plugin...")
    print()

    # Get paths
    repo_root = Path(__file__).parent.parent
    hooks_source = repo_root / ".github" / "workflows" / ".claude" / "hooks"
    plugin_source = repo_root / "claude-code-plugins" / "essentials"
    marketplace_source = repo_root / ".claude-plugin" / "marketplace.json"

    claude_home = Path.home() / ".claude"
    hooks_dest = claude_home / "hooks"
    plugins_dir = claude_home / "plugins"
    marketplace_dest = plugins_dir / "sisyphus-marketplace"

    # Verify source files exist
    if not hooks_source.exists():
        print(f"❌ Error: Hooks directory not found at {hooks_source}")
        return 1

    if not plugin_source.exists():
        print(f"❌ Error: Plugin directory not found at {plugin_source}")
        return 1

    # Create directories if they don't exist
    claude_home.mkdir(exist_ok=True)
    plugins_dir.mkdir(exist_ok=True)

    # Step 1: Copy hooks
    print("📋 Step 1: Installing Claude Code hooks...")
    if hooks_dest.exists():
        if args.force:
            shutil.rmtree(hooks_dest)
            shutil.copytree(hooks_source, hooks_dest)
            print(f"  ✅ Hooks copied to {hooks_dest}")
        else:
            response = input(f"  Hooks directory already exists at {hooks_dest}. Overwrite? [y/N]: ")
            if response.lower() != "y":
                print("  ⏭️  Skipping hooks installation")
            else:
                shutil.rmtree(hooks_dest)
                shutil.copytree(hooks_source, hooks_dest)
                print(f"  ✅ Hooks copied to {hooks_dest}")
    else:
        shutil.copytree(hooks_source, hooks_dest)
        print(f"  ✅ Hooks copied to {hooks_dest}")

    # Step 2: Install plugin
    print()
    print("📦 Step 2: Installing essentials plugin...")

    # Create marketplace directory
    marketplace_dest.mkdir(parents=True, exist_ok=True)

    # Copy marketplace.json
    if marketplace_source.exists():
        shutil.copy(marketplace_source, marketplace_dest / "marketplace.json")
        print(f"  ✅ Marketplace configuration copied")

    # Copy plugin files
    plugin_dest = marketplace_dest / "claude-code-plugins" / "essentials"
    if plugin_dest.exists():
        if args.force:
            shutil.rmtree(plugin_dest)
            shutil.copytree(plugin_source, plugin_dest)
            print(f"  ✅ Plugin copied to {plugin_dest}")
        else:
            response = input(f"  Plugin already exists at {plugin_dest}. Overwrite? [y/N]: ")
            if response.lower() != "y":
                print("  ⏭️  Skipping plugin installation")
            else:
                shutil.rmtree(plugin_dest)
                shutil.copytree(plugin_source, plugin_dest)
                print(f"  ✅ Plugin copied to {plugin_dest}")
    else:
        plugin_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(plugin_source, plugin_dest)
        print(f"  ✅ Plugin copied to {plugin_dest}")

    # Step 3: Update settings.json to include the marketplace
    print()
    print("⚙️  Step 3: Updating Claude Code settings...")
    settings_path = claude_home / "settings.json"

    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
    else:
        settings = {}

    # Add marketplace to extraKnownMarketplaces
    if "extraKnownMarketplaces" not in settings:
        settings["extraKnownMarketplaces"] = {}

    settings["extraKnownMarketplaces"]["sisyphus-marketplace"] = {
        "source": {
            "type": "local",
            "path": str(marketplace_dest)
        }
    }

    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"  ✅ Settings updated at {settings_path}")

    # Final message
    print()
    print("✨ Setup complete!")
    print()
    print("Next steps:")
    print("1. Restart Claude Code if it's running")
    print("2. The following commands and agents are now available:")
    print("   Commands: /execute, /plan")
    print("   Agents: architect, executor, plan-reviewer")
    print()
    print("3. Required dependencies for hooks:")
    print("   - Python 3.12+")
    print("   - uv (Python package manager)")
    print("   - Install dependencies: uv sync")
    print()
    print("Happy coding! 🎉")

    return 0


if __name__ == "__main__":
    sys.exit(main())
