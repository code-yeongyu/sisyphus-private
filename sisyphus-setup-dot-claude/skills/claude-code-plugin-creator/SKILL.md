---
name: claude-code-plugin-creator
description: Claude Code Plugin Creator, as known as 'CC Plugin Master'. Create, package, and publish Claude Code plugins and marketplaces to GitHub. Use when building new plugins from scratch, wrapping existing configurations as plugins, setting up plugin marketplaces, or publishing plugins to GitHub repositories.
---

# Claude Code Plugin Creator

Create and publish Claude Code plugins and marketplaces. This skill provides scripts and workflows for the complete plugin development lifecycle.

## Understanding Plugin Directory Structure First

**CRITICAL**: Before using any scripts, understand that Claude Code plugins have a specific structure:

```
my-plugin/                        # Plugin root directory
├── .claude-plugin/               # Metadata directory (REQUIRED)
│   └── plugin.json              # Plugin manifest (REQUIRED)
├── commands/                     # Slash commands (optional, auto-discovered)
│   ├── deploy.md
│   └── status.md
├── agents/                       # Subagents (optional, auto-discovered)
│   ├── reviewer.md
│   └── tester.md
├── skills/                       # Agent Skills (optional, auto-discovered)
│   ├── code-reviewer/
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── pdf-processor/
│       └── SKILL.md
├── hooks/                        # Hook configurations (optional)
│   ├── hooks.json               # Auto-discovered if exists
│   └── custom-hooks.json        # Requires plugin.json reference
├── .mcp.json                    # MCP servers (optional, auto-discovered)
├── scripts/                      # Utility scripts for hooks
│   ├── format.py
│   └── lint.sh
└── README.md                     # Documentation
```

**Key Rules**:
1. `.claude-plugin/` directory contains ONLY `plugin.json` - nothing else
2. ALL other directories (`commands/`, `agents/`, `skills/`, `hooks/`) go at plugin root
3. Default files are auto-discovered (no need to specify in plugin.json):
   - `hooks/hooks.json`
   - `.mcp.json`
4. Only specify paths in plugin.json when using non-default locations

## Quick Start Scripts

**Location**: All scripts are in the `scripts/` directory of this skill

### Create a New Plugin

```bash
# Basic usage (creates in current directory)
python ~/.claude/skills/claude-code-plugin-creator/scripts/init_plugin.py my-plugin

# Specify output directory
python ~/.claude/skills/claude-code-plugin-creator/scripts/init_plugin.py my-plugin --path ./output
```

**What it creates**:
```
my-plugin/
├── .claude-plugin/plugin.json    # ✅ Manifest with TODO placeholders
├── commands/example.md           # ✅ Example command template
├── agents/example-agent.md       # ✅ Example agent template
├── skills/example-skill/SKILL.md # ✅ Example skill template
├── hooks/hooks.json              # ✅ Hook configuration with example
├── scripts/example-hook.sh       # ✅ Example hook script (executable)
├── .mcp.json                     # ✅ MCP server template
└── README.md                     # ✅ Documentation template
```

### Create a Marketplace

```bash
# Basic usage
python ~/.claude/skills/claude-code-plugin-creator/scripts/init_marketplace.py my-marketplace

# Specify output directory
python ~/.claude/skills/claude-code-plugin-creator/scripts/init_marketplace.py my-marketplace --path ./output
```

**What it creates**:
```
my-marketplace/
├── .claude-plugin/marketplace.json  # ✅ Marketplace manifest
├── plugins/                         # ✅ Directory for plugin repos
└── README.md                        # ✅ Documentation template
```

### Validate Plugin or Marketplace

```bash
# Validate plugin
python ~/.claude/skills/claude-code-plugin-creator/scripts/validate.py ./my-plugin

# Validate marketplace
python ~/.claude/skills/claude-code-plugin-creator/scripts/validate.py ./my-marketplace --type marketplace

# Auto-detect type
python ~/.claude/skills/claude-code-plugin-creator/scripts/validate.py ./path --type auto
```

## Complete Workflows

### Workflow 1: Create Plugin from Scratch

**Step 1: Initialize plugin structure**
```bash
# Run the init script
python ~/.claude/skills/claude-code-plugin-creator/scripts/init_plugin.py awesome-tools --path ~/projects
cd ~/projects/awesome-tools
```

**Step 2: Update plugin metadata**
Edit `.claude-plugin/plugin.json`:
```json
{
  "name": "awesome-tools",
  "version": "1.0.0",
  "description": "Deployment and monitoring tools",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "homepage": "https://github.com/you/awesome-tools",
  "repository": "https://github.com/you/awesome-tools",
  "license": "MIT",
  "keywords": ["deployment", "monitoring"]
}
```

**Step 3: Add your components**

**Commands** (`commands/` directory):
- Create `.md` files with frontmatter
- Example: `commands/deploy.md`
```markdown
---
description: Deploy application to production
---

# Deploy Command

Execute deployment script and verify status.
```

**Agents** (`agents/` directory):
- Create `.md` files with frontmatter
- Example: `agents/deployment-expert.md`
```markdown
---
description: Expert in deployment strategies
capabilities: ["deploy", "rollback", "monitor"]
---

# Deployment Expert

Specialized agent for handling deployments.
```

**Skills** (`skills/` directory):
- Create subdirectory with `SKILL.md`
- Example: `skills/deployment-skill/SKILL.md`
```markdown
---
name: deployment-skill
description: Handle deployment workflows
---

# Deployment Skill

Instructions for deployment process.
```

**Hooks** (`hooks/hooks.json`):
```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
        }
      ]
    }
  ]
}
```

**MCP Servers** (`.mcp.json` at root):
```json
{
  "mcpServers": {
    "deployment-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/deploy-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

**Step 4: Validate plugin structure**
```bash
python ~/.claude/skills/claude-code-plugin-creator/scripts/validate.py ~/projects/awesome-tools
```

**Step 5: Test locally with marketplace**
```bash
# Create test marketplace
cd ~/projects
python ~/.claude/skills/claude-code-plugin-creator/scripts/init_marketplace.py test-marketplace
cd test-marketplace
```

Edit `.claude-plugin/marketplace.json`:
```json
{
  "name": "test-marketplace",
  "plugins": [
    {
      "name": "awesome-tools",
      "source": "../awesome-tools",
      "description": "Deployment and monitoring tools"
    }
  ]
}
```

**Step 6: Install in Claude Code**
```
/plugin marketplace add ~/projects/test-marketplace
/plugin install awesome-tools@test-marketplace
```

### Workflow 2: Package Existing .claude Configuration

**Step 1: Identify components to package**
```bash
# Check what you have in ~/.claude/
ls ~/.claude/commands/     # Slash commands
ls ~/.claude/hooks/        # Hook configurations
cat ~/.claude/settings.json | grep -A 20 mcpServers  # MCP servers
```

**Step 2: Create plugin structure**
```bash
python ~/.claude/skills/claude-code-plugin-creator/scripts/init_plugin.py my-existing-setup --path ~/projects
cd ~/projects/my-existing-setup
```

**Step 3: Copy components to correct locations**

**Copy commands**:
```bash
# Commands go in commands/ directory at plugin root
cp ~/.claude/commands/*.md ~/projects/my-existing-setup/commands/
# Remove the example.md template if not needed
rm ~/projects/my-existing-setup/commands/example.md
```

**Copy hooks**:
```bash
# Copy hook JSON configs
cp ~/.claude/hooks/hooks.json ~/projects/my-existing-setup/hooks/

# Copy hook scripts
mkdir -p ~/projects/my-existing-setup/scripts
cp ~/.claude/hooks/*.sh ~/projects/my-existing-setup/scripts/
cp ~/.claude/hooks/*.py ~/projects/my-existing-setup/scripts/

# Update hooks.json to use ${CLAUDE_PLUGIN_ROOT}
# Change: "script": "/Users/you/.claude/hooks/format.sh"
# To: "script": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
```

**Extract MCP servers**:
```bash
# Extract mcpServers section from settings.json to .mcp.json
# From ~/.claude/settings.json:
{
  "mcpServers": {
    "my-server": {
      "command": "...",
      "args": [...]
    }
  }
}

# To ~/projects/my-existing-setup/.mcp.json:
{
  "mcpServers": {
    "my-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/my-server",
      "args": ["${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

**Step 4: Update plugin.json metadata**
```bash
# Edit .claude-plugin/plugin.json
{
  "name": "my-existing-setup",
  "version": "1.0.0",
  "description": "My personal Claude Code setup",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  }
}
```

**Step 5: Validate**
```bash
python ~/.claude/skills/claude-code-plugin-creator/scripts/validate.py ~/projects/my-existing-setup
```

**Step 6: Test locally**
```bash
# Create marketplace for testing
cd ~/projects
python ~/.claude/skills/claude-code-plugin-creator/scripts/init_marketplace.py my-marketplace
cd my-marketplace

# Edit .claude-plugin/marketplace.json
{
  "name": "my-marketplace",
  "plugins": [
    {
      "name": "my-existing-setup",
      "source": "../my-existing-setup"
    }
  ]
}

# Install in Claude Code
# In Claude Code terminal:
/plugin marketplace add ~/projects/my-marketplace
/plugin install my-existing-setup@my-marketplace
```

### Workflow 3: Publish to GitHub

**Step 1: Prepare repository**
```bash
cd ~/projects/my-plugin

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial plugin release v1.0.0"
```

**Step 2: Create GitHub repository**
```bash
# Using GitHub CLI (recommended)
gh repo create my-username/my-plugin --public --source=. --remote=origin --push

# Or manually:
# 1. Create repo on github.com
# 2. Add remote: git remote add origin https://github.com/my-username/my-plugin.git
# 3. Push: git push -u origin main
```

**Step 3: Users install your plugin**

**Option A: Direct marketplace installation**
```
# Users add your repository as a marketplace
/plugin marketplace add my-username/my-plugin
```

**Option B: Add to existing marketplace**
If you have a marketplace repository, update its `.claude-plugin/marketplace.json`:
```json
{
  "name": "my-marketplace",
  "plugins": [
    {
      "name": "my-plugin",
      "source": {
        "source": "github",
        "repo": "my-username/my-plugin"
      },
      "description": "Plugin description here"
    }
  ]
}
```

Then users install via:
```
/plugin marketplace add my-username/my-marketplace
/plugin install my-plugin@my-marketplace
```

**Step 4: Version management**
```bash
# Update version in .claude-plugin/plugin.json
{
  "version": "1.1.0"
}

# Commit and tag
git add .
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

## Reference Documentation

All reference documents are in `references/` directory:

- `plugin.md` - Complete plugin development guide
- `plugins-reference.md` - Technical specifications and schemas
- `plugin-marketplaces.md` - Marketplace creation and management

Read these for:
- Detailed component specs (commands, agents, skills, hooks, MCP)
- Advanced plugin organization patterns
- Marketplace configuration options
- Team distribution strategies

## Scripts Reference

### init_plugin.py

```bash
python scripts/init_plugin.py <plugin-name> [--path <output-dir>]
```

Creates new plugin with complete directory structure.

### init_marketplace.py

```bash
python scripts/init_marketplace.py <marketplace-name> [--path <output-dir>]
```

Creates new marketplace with manifest and plugins directory.

### validate.py

```bash
python scripts/validate.py <path> [--type plugin|marketplace|auto]
```

Validates plugin or marketplace structure and manifests.

## Component-by-Component Guide

### Commands Component (`commands/` directory)

**What**: Slash commands that users can invoke in Claude Code

**Location**: `commands/` directory at plugin root

**File format**: Markdown files with YAML frontmatter

**Example**: `commands/deploy.md`
```markdown
---
description: Deploy application to production environment
---

# Deploy Command

Execute the following deployment workflow:

1. Run pre-deployment checks
2. Build the application
3. Upload to production server
4. Run health checks
5. Notify team of deployment status

Use environment variables for configuration.
```

**Auto-discovery**: All `.md` files in `commands/` are automatically loaded

**Custom paths**: Add to plugin.json only if using non-standard locations:
```json
{
  "commands": ["./custom/path/special-command.md"]
}
```

### Agents Component (`agents/` directory)

**What**: Specialized subagents Claude can invoke for specific tasks

**Location**: `agents/` directory at plugin root

**File format**: Markdown files with YAML frontmatter

**Example**: `agents/security-reviewer.md`
```markdown
---
description: Security expert specialized in code vulnerability analysis
capabilities: ["security-audit", "vulnerability-scan", "penetration-testing"]
---

# Security Reviewer Agent

Expert in identifying security vulnerabilities and suggesting fixes.

## Capabilities
- SQL injection detection
- XSS vulnerability analysis
- Authentication/authorization review
- Dependency vulnerability scanning

## When to use
Invoke when analyzing code for security issues or reviewing PRs.
```

**Auto-discovery**: All `.md` files in `agents/` are automatically loaded

### Skills Component (`skills/` directory)

**What**: Agent Skills that extend Claude's capabilities autonomously

**Location**: `skills/` directory at plugin root

**Structure**: Each skill is a subdirectory with `SKILL.md`

**Example**: `skills/deployment-expert/SKILL.md`
```markdown
---
name: deployment-expert
description: Handle production deployment workflows with rollback capabilities
---

# Deployment Expert Skill

Specialized in managing production deployments.

## Workflow
1. Pre-deployment validation
2. Staged rollout
3. Health monitoring
4. Automatic rollback on errors

## Usage
Claude autonomously uses this when deployment tasks are detected.
```

**Auto-discovery**: All `SKILL.md` files in `skills/*/` are automatically loaded

**Supporting files**: Can include `scripts/`, `references/`, `assets/` within skill directory

### Hooks Component (`hooks/` directory)

**What**: Event handlers that run automatically on Claude Code events

**Location**: `hooks/hooks.json` at plugin root (auto-discovered)

**Format**: JSON configuration with matchers and hook definitions

**Example**: `hooks/hooks.json`
```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
        }
      ]
    }
  ],
  "UserPromptSubmit": [
    {
      "matcher": ".*",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/inject-context.py"
        }
      ]
    }
  ]
}
```

**Available events**:
- `PreToolUse`: Before tool execution
- `PostToolUse`: After tool execution
- `UserPromptSubmit`: When user submits prompt
- `Notification`: On notifications
- `Stop`: When Claude stops
- `SubagentStop`: When subagent stops
- `SessionStart`: Session beginning
- `SessionEnd`: Session ending
- `PreCompact`: Before history compaction

**Hook scripts**: Place in `scripts/` directory, reference with `${CLAUDE_PLUGIN_ROOT}`

**Script example**: `scripts/format.sh`
```bash
#!/bin/bash
# Auto-format Python files after Write/Edit

# Access hook environment variables
FILE_PATH="$CLAUDE_TOOL_FILE_PATH"

if [[ "$FILE_PATH" == *.py ]]; then
    ruff format "$FILE_PATH"
    ruff check --fix "$FILE_PATH"
fi
```

### MCP Servers Component (`.mcp.json`)

**What**: Model Context Protocol servers for external tool integration

**Location**: `.mcp.json` at plugin root (auto-discovered)

**Format**: Standard MCP server configuration

**Example**: `.mcp.json`
```json
{
  "mcpServers": {
    "deployment-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/deploy-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DATA_PATH": "${CLAUDE_PLUGIN_ROOT}/data",
        "LOG_LEVEL": "info"
      }
    },
    "monitoring-client": {
      "command": "npx",
      "args": ["@company/monitoring-mcp"],
      "cwd": "${CLAUDE_PLUGIN_ROOT}"
    }
  }
}
```

**Environment variables**: Always use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths

## Plugin Manifest (`plugin.json`) Reference

**Location**: `.claude-plugin/plugin.json` (REQUIRED)

**Valid fields**:
```json
{
  "name": "plugin-name",                    // REQUIRED: kebab-case, no spaces
  "version": "1.0.0",                       // Semantic versioning
  "description": "Plugin description",      // Brief explanation
  "author": {                               // Author information
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://github.com/you"
  },
  "homepage": "https://docs.example.com",   // Documentation URL
  "repository": "https://github.com/you/plugin", // Source code
  "license": "MIT",                         // License identifier
  "keywords": ["deployment", "automation"], // Discovery tags

  // Optional: Only for non-default paths
  "commands": ["./custom/commands/special.md"],
  "agents": ["./custom/agents/expert.md"],
  "hooks": "./config/hooks.json",
  "mcpServers": "./config/mcp.json"
}
```

**INVALID fields** (do NOT include):
- `configuration`
- `files`
- `claudeCodeVersion`
- `dependencies`

**Auto-discovered paths** (no need to specify):
- `commands/` directory → all `.md` files
- `agents/` directory → all `.md` files
- `skills/` directory → all `*/SKILL.md` files
- `hooks/hooks.json` → if exists
- `.mcp.json` → if exists

## Environment Variables Guide

### ${CLAUDE_PLUGIN_ROOT}

**Purpose**: Absolute path to plugin installation directory

**Where to use**: JSON configuration files (hooks.json, .mcp.json, plugin.json)

**Example in hooks.json**:
```json
{
  "PostToolUse": [
    {
      "hooks": [
        {
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.py"
        }
      ]
    }
  ]
}
```

**Example in .mcp.json**:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DATA_PATH": "${CLAUDE_PLUGIN_ROOT}/data"
      }
    }
  }
}
```

### Environment Variables in Hook Scripts

**CRITICAL**: `${CLAUDE_PLUGIN_ROOT}` is NOT available as runtime environment variable in hook scripts

**Solution**: Calculate plugin root using `__file__`

**Python example**:
```python
#!/usr/bin/env python3
from pathlib import Path

# Calculate plugin root based on script location
# If script is at: plugin-root/scripts/format.py
plugin_root = Path(__file__).parent.parent

# If script is at: plugin-root/hooks/post-tool-use/format.py
# plugin_root = Path(__file__).parent.parent.parent

# Now use plugin_root to access plugin files
config_file = plugin_root / "config" / "settings.json"
```

**Bash example**:
```bash
#!/bin/bash

# Calculate plugin root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Use plugin root
CONFIG_FILE="$PLUGIN_ROOT/config/settings.json"
```

## Advanced Patterns

### Pattern 1: Global Override with Plugin Fallback

**Use case**: Allow users to override plugin defaults with their own global configurations

**Implementation**:
```python
from pathlib import Path

def get_language_guide(extension: str) -> Path | None:
    # Priority 1: User's global override
    global_file = Path.home() / ".claude" / "modular-prompts" / "languages" / f"{extension}.md"
    if global_file.exists():
        return global_file

    # Priority 2: Plugin bundled default
    plugin_root = Path(__file__).parent.parent.parent
    plugin_file = plugin_root / "modular-prompts" / "languages" / f"{extension}.md"
    if plugin_file.exists():
        return plugin_file

    return None
```

**Common use cases**:
- Language guides: `~/.claude/modular-prompts/languages/*.md` → `plugin/modular-prompts/languages/*.md`
- Static checkers: `~/.claude/hooks/post-tool-use/static_check/` → `plugin/hooks/post-tool-use/static_check/`
- Configuration files: `~/.claude/configs/` → `plugin/configs/`

**Benefits**:
- Users customize without modifying plugin
- Plugins provide sensible defaults
- User customizations survive plugin updates

### Pattern 2: Multi-Plugin Marketplace

**Structure**:
```
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    ├── deployment-tools/
    ├── monitoring-utils/
    └── security-suite/
```

**marketplace.json**:
```json
{
  "name": "my-marketplace",
  "plugins": [
    {
      "name": "deployment-tools",
      "source": "./plugins/deployment-tools",
      "description": "Deployment automation tools"
    },
    {
      "name": "monitoring-utils",
      "source": "./plugins/monitoring-utils",
      "description": "Monitoring and observability utilities"
    },
    {
      "name": "security-suite",
      "source": "./plugins/security-suite",
      "description": "Security scanning and compliance"
    }
  ]
}
```

### Pattern 3: External Plugin References

**Marketplace referencing external plugins**:
```json
{
  "name": "company-marketplace",
  "plugins": [
    {
      "name": "local-plugin",
      "source": "./plugins/local-plugin"
    },
    {
      "name": "github-plugin",
      "source": {
        "source": "github",
        "repo": "company/github-plugin"
      }
    },
    {
      "name": "git-plugin",
      "source": {
        "source": "url",
        "url": "https://gitlab.com/company/git-plugin.git"
      }
    }
  ]
}
```

## Plugin Source Types

**Local path**:
```json
{
  "source": "./plugins/my-plugin"
}
```

**GitHub repository**:
```json
{
  "source": {
    "source": "github",
    "repo": "username/plugin-name"
  }
}
```

**Git URL**:
```json
{
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git"
  }
}
```

## Troubleshooting Guide

### Plugin Not Loading

**Problem**: Plugin doesn't appear in `/plugin` list

**Solutions**:
1. Verify `.claude-plugin/plugin.json` exists
   ```bash
   ls -la ~/projects/my-plugin/.claude-plugin/plugin.json
   ```

2. Validate JSON syntax
   ```bash
   python ~/.claude/skills/claude-code-plugin-creator/scripts/validate.py ~/projects/my-plugin
   ```

3. Check plugin.json has required `name` field
   ```json
   {
     "name": "my-plugin"  // REQUIRED
   }
   ```

4. Ensure plugin name uses kebab-case (no spaces)
   ```json
   // ✅ Correct
   "name": "deployment-tools"

   // ❌ Wrong
   "name": "deployment tools"
   "name": "Deployment_Tools"
   ```

### Commands Not Appearing

**Problem**: Slash commands don't show up in Claude Code

**Solutions**:
1. Verify `commands/` directory is at plugin root, NOT in `.claude-plugin/`
   ```
   ✅ Correct structure:
   my-plugin/
   ├── .claude-plugin/plugin.json
   └── commands/deploy.md

   ❌ Wrong structure:
   my-plugin/
   └── .claude-plugin/
       ├── plugin.json
       └── commands/deploy.md  # Wrong location!
   ```

2. Check command files have `.md` extension

3. Verify frontmatter syntax
   ```markdown
   ---
   description: Command description here
   ---

   # Command body
   ```

4. If using custom paths, verify plugin.json references them
   ```json
   {
     "commands": ["./custom/path/command.md"]
   }
   ```

### Hooks Not Firing

**Problem**: Hook scripts don't execute

**Solutions**:
1. Make scripts executable
   ```bash
   chmod +x ~/projects/my-plugin/scripts/*.sh
   chmod +x ~/projects/my-plugin/scripts/*.py
   ```

2. Verify `${CLAUDE_PLUGIN_ROOT}` in hooks.json
   ```json
   {
     "hooks": [
       {
         "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"  // ✅ Correct
       }
     ]
   }
   ```

3. Check hook script has proper shebang
   ```bash
   #!/bin/bash
   # or
   #!/usr/bin/env python3
   ```

4. Test hook script manually
   ```bash
   ~/projects/my-plugin/scripts/format.sh
   ```

5. Check hook matcher pattern
   ```json
   {
     "matcher": "Write|Edit",  // Regex pattern
     "hooks": [...]
   }
   ```

### MCP Server Fails to Start

**Problem**: MCP server doesn't initialize

**Solutions**:
1. Use `${CLAUDE_PLUGIN_ROOT}` for all plugin paths
   ```json
   {
     "mcpServers": {
       "my-server": {
         "command": "${CLAUDE_PLUGIN_ROOT}/servers/server",  // ✅ Correct
         "args": ["${CLAUDE_PLUGIN_ROOT}/config.json"]
       }
     }
   }
   ```

2. Verify server binary exists and is executable
   ```bash
   ls -la ~/projects/my-plugin/servers/server
   chmod +x ~/projects/my-plugin/servers/server
   ```

3. Check server logs with `claude --debug`
   ```bash
   claude --debug
   ```

4. Test server manually
   ```bash
   ~/projects/my-plugin/servers/server --config ~/projects/my-plugin/config.json
   ```

### Marketplace Not Found

**Problem**: Marketplace doesn't load

**Solutions**:
1. Verify `.claude-plugin/marketplace.json` exists
   ```bash
   ls -la ~/projects/my-marketplace/.claude-plugin/marketplace.json
   ```

2. Check marketplace.json structure
   ```json
   {
     "name": "my-marketplace",  // Required
     "plugins": [               // Required (can be empty array)
       {
         "name": "plugin-name",
         "source": "./plugins/plugin-name"
       }
     ]
   }
   ```

3. Validate marketplace
   ```bash
   python ~/.claude/skills/claude-code-plugin-creator/scripts/validate.py ~/projects/my-marketplace --type marketplace
   ```

### Skills Not Auto-Loading

**Problem**: Agent Skills don't trigger

**Solutions**:
1. Verify skill structure
   ```
   my-plugin/
   └── skills/
       └── my-skill/
           └── SKILL.md  // Must be exactly "SKILL.md"
   ```

2. Check SKILL.md frontmatter
   ```markdown
   ---
   name: my-skill          # Required
   description: When to use this skill  # Required
   ---
   ```

3. Ensure skill name matches directory name
   ```
   skills/deployment-expert/SKILL.md
   ---
   name: deployment-expert  # Must match directory name
   ---
   ```

### Path Resolution Issues

**Problem**: Plugin can't find its own files

**Solutions**:
1. In Python scripts, calculate plugin root
   ```python
   from pathlib import Path

   # If script at: plugin-root/scripts/tool.py
   plugin_root = Path(__file__).parent.parent

   # If script at: plugin-root/hooks/post-tool-use/hook.py
   plugin_root = Path(__file__).parent.parent.parent
   ```

2. In Bash scripts, calculate plugin root
   ```bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
   ```

3. Never use absolute paths in distributed plugins
   ```bash
   # ❌ Wrong - breaks on other machines
   CONFIG="/Users/you/projects/my-plugin/config.json"

   # ✅ Correct - portable
   CONFIG="$PLUGIN_ROOT/config.json"
   ```

### Debugging Tips

**Enable debug mode**:
```bash
claude --debug
```

**Check plugin installation**:
```
/plugin list
```

**Validate before distributing**:
```bash
python ~/.claude/skills/claude-code-plugin-creator/scripts/validate.py ./my-plugin
```

**Test locally first**:
Always test with local marketplace before pushing to GitHub

For detailed technical specifications, see `references/plugins-reference.md`
