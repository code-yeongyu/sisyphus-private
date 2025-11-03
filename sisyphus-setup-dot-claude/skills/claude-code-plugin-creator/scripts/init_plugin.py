#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


def create_plugin_structure(plugin_name: str, output_dir: Path) -> None:
    plugin_dir = output_dir / plugin_name
    if plugin_dir.exists():
        print(f"❌ Error: Plugin directory already exists: {plugin_dir}")
        sys.exit(1)

    print(f"🚀 Creating plugin: {plugin_name}")
    print(f"   Location: {plugin_dir}\n")

    plugin_dir.mkdir(parents=True)
    (plugin_dir / ".claude-plugin").mkdir()
    (plugin_dir / "commands").mkdir()
    (plugin_dir / "agents").mkdir()
    (plugin_dir / "skills").mkdir()
    (plugin_dir / "hooks").mkdir()
    (plugin_dir / "scripts").mkdir()

    manifest = {
        "name": plugin_name,
        "version": "1.0.0",
        "description": "TODO: Add plugin description",
        "author": {"name": "TODO: Your Name", "email": "TODO: your.email@example.com"},
        "homepage": f"https://github.com/TODO/{plugin_name}",
        "repository": f"https://github.com/TODO/{plugin_name}",
        "license": "MIT",
        "keywords": [],
    }

    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"✅ Created: {manifest_path.relative_to(output_dir)}")

    example_command = """---
description: TODO: Describe what this command does
---

# Example Command

TODO: Add instructions for Claude on how to execute this command.

This is a template command. Customize it for your plugin's needs.
"""

    command_path = plugin_dir / "commands" / "example.md"
    with open(command_path, "w") as f:
        f.write(example_command)
    print(f"✅ Created: {command_path.relative_to(output_dir)}")

    example_agent = """---
description: TODO: Describe this agent's specialization
capabilities: ["task1", "task2", "task3"]
---

# Example Agent

TODO: Detailed description of the agent's role, expertise, and when Claude should invoke it.

## Capabilities
- TODO: Specific task the agent excels at
- TODO: Another specialized capability
- TODO: When to use this agent vs others

## Context and examples
TODO: Provide examples of when this agent should be used and what kinds of problems it solves.
"""

    agent_path = plugin_dir / "agents" / "example-agent.md"
    with open(agent_path, "w") as f:
        f.write(example_agent)
    print(f"✅ Created: {agent_path.relative_to(output_dir)}")

    hooks_config = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Write|Edit",
                    "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/example-hook.sh"}],
                }
            ]
        }
    }

    hooks_path = plugin_dir / "hooks" / "hooks.json"
    with open(hooks_path, "w") as f:
        json.dump(hooks_config, f, indent=2)
    print(f"✅ Created: {hooks_path.relative_to(output_dir)}")

    example_hook = """#!/bin/bash
# Example hook script
# This script runs after Write or Edit tool usage

echo "Hook executed: example-hook.sh"
# Add your custom logic here
"""

    hook_script_path = plugin_dir / "scripts" / "example-hook.sh"
    with open(hook_script_path, "w") as f:
        f.write(example_hook)
    hook_script_path.chmod(0o755)
    print(f"✅ Created: {hook_script_path.relative_to(output_dir)}")

    mcp_config = {
        "mcpServers": {
            f"{plugin_name}-server": {
                "command": "${CLAUDE_PLUGIN_ROOT}/servers/example-server",
                "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
                "env": {"DATA_PATH": "${CLAUDE_PLUGIN_ROOT}/data"},
            }
        }
    }

    mcp_path = plugin_dir / ".mcp.json"
    with open(mcp_path, "w") as f:
        json.dump(mcp_config, f, indent=2)
    print(f"✅ Created: {mcp_path.relative_to(output_dir)}")

    readme = rf"""# {plugin_name}

TODO: Add plugin description

## Installation

\`\`\`shell
/plugin marketplace add <your-marketplace>
/plugin install {plugin_name}@<your-marketplace>
\`\`\`

## Features

- TODO: List plugin features
- TODO: Add more features

## Usage

TODO: Add usage examples

## License

MIT
"""

    readme_path = plugin_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme)
    print(f"✅ Created: {readme_path.relative_to(output_dir)}")

    skill_dir = plugin_dir / "skills" / "example-skill"
    skill_dir.mkdir(parents=True)

    skill_md = """---
name: example-skill
description: TODO: Describe when Claude should use this skill
---

# Example Skill

TODO: Add instructions for using this skill.

## Usage

TODO: Provide usage examples and guidance.
"""

    skill_md_path = skill_dir / "SKILL.md"
    with open(skill_md_path, "w") as f:
        f.write(skill_md)
    print(f"✅ Created: {skill_md_path.relative_to(output_dir)}")

    print(f"\n✨ Plugin '{plugin_name}' created successfully!")
    print("\n📝 Next steps:")
    print(f"   1. Edit {manifest_path.relative_to(output_dir)} to update plugin metadata")
    print("   2. Customize or remove example files in:")
    print("      - commands/")
    print("      - agents/")
    print("      - skills/")
    print("      - hooks/")
    print("   3. Update .mcp.json if you need MCP server integration")
    print("   4. Test your plugin locally before publishing")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a new Claude Code plugin structure")
    parser.add_argument("plugin_name", help="Name of the plugin (kebab-case recommended)")
    parser.add_argument(
        "--path", type=Path, default=Path.cwd(), help="Output directory for the plugin (default: current directory)"
    )

    args = parser.parse_args()

    if " " in args.plugin_name:
        print("❌ Error: Plugin name cannot contain spaces. Use kebab-case (e.g., my-plugin)")
        sys.exit(1)

    create_plugin_structure(args.plugin_name, args.path)


if __name__ == "__main__":
    main()
