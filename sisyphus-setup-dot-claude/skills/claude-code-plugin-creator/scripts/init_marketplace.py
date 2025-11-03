#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


def create_marketplace_structure(marketplace_name: str, output_dir: Path) -> None:
    marketplace_dir = output_dir / marketplace_name
    if marketplace_dir.exists():
        print(f"❌ Error: Marketplace directory already exists: {marketplace_dir}")
        sys.exit(1)

    print(f"🚀 Creating marketplace: {marketplace_name}")
    print(f"   Location: {marketplace_dir}\n")

    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / ".claude-plugin").mkdir()
    (marketplace_dir / "plugins").mkdir()

    marketplace_config = {
        "name": marketplace_name,
        "owner": {"name": "TODO: Your Name", "email": "TODO: your.email@example.com"},
        "metadata": {
            "description": "TODO: Add marketplace description",
            "version": "1.0.0",
            "pluginRoot": "./plugins",
        },
        "plugins": [],
    }

    config_path = marketplace_dir / ".claude-plugin" / "marketplace.json"
    with open(config_path, "w") as file:
        json.dump(marketplace_config, file, indent=2)
    print(f"✅ Created: {config_path.relative_to(output_dir)}")

    readme = rf"""# {marketplace_name}

TODO: Add marketplace description

## Available Plugins

TODO: List plugins available in this marketplace

## Usage

Add this marketplace to Claude Code:

\`\`\`shell
/plugin marketplace add <your-repo-url or local-path>
\`\`\`

Browse plugins:

\`\`\`shell
/plugin
\`\`\`

Install plugins:

\`\`\`shell
/plugin install <plugin-name>@{marketplace_name}
\`\`\`

## Contributing

TODO: Add contribution guidelines

## License

MIT
"""

    readme_path = marketplace_dir / "README.md"
    with open(readme_path, "w") as file:
        file.write(readme)
    print(f"✅ Created: {readme_path.relative_to(output_dir)}")

    print(f"\n✨ Marketplace '{marketplace_name}' created successfully!")
    print("\n📝 Next steps:")
    print(f"   1. Edit {config_path.relative_to(output_dir)} to update marketplace metadata")
    print("   2. Add plugins to the plugins/ directory")
    print("   3. Register plugins in marketplace.json")
    print("   4. Commit and push to GitHub for distribution")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a new Claude Code plugin marketplace")
    parser.add_argument("marketplace_name", help="Name of the marketplace (kebab-case recommended)")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Output directory for the marketplace (default: current directory)",
    )

    args = parser.parse_args()

    if " " in args.marketplace_name:
        print("❌ Error: Marketplace name cannot contain spaces. Use kebab-case (e.g., my-marketplace)")
        sys.exit(1)

    create_marketplace_structure(args.marketplace_name, args.path)


if __name__ == "__main__":
    main()
