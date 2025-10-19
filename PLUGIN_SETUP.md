# Sisyphus Claude Code Plugin Setup

This guide explains how to install and use the Sisyphus essential Claude Code plugin.

## What Gets Installed

The Sisyphus essential plugin provides specialized tools for AI-driven development:

### 1. Custom Hooks

Located in `.github/workflows/.claude/hooks/`, these hooks enforce code quality:

**Pre-Tool-Use Hooks:**
- `block_asyncio_when_anyio_exists.py` - Enforces anyio usage over asyncio for backend compatibility
- `block_json_when_orjson_exists.py` - Enforces orjson usage for better performance

**Post-Tool-Use Hooks:**
- Static checks for Python (ruff, basedpyright, opinionated rules)
- TypeScript/Terraform static checks
- Code quality reminders (tmux usage, conftest injection, encoding checks)
- Language-specific guidance injection

**User-Prompt-Submit Hooks:**
- System reminders for better development workflow

### 2. Commands

Slash commands that provide specialized prompts:

- `/execute` - Execute tasks from ai-todolist.md with full context
- `/plan` - Create detailed work plans for complex features

### 3. Agents

Pre-configured agent personas for the two-phase workflow:

- `architect` - Verification agent that reviews completed work critically
- `executor` - Execution agent that focuses on implementing tasks
- `plan-reviewer` - Reviews and improves work plans

### 4. MCP Server

- `context7` - Library documentation retrieval system for up-to-date docs

## Installation

### Quick Setup

```bash
# From the sisyphus repository root
python scripts/setup-claude-plugin.py
```

The script will:
1. Copy hooks to `~/.claude/hooks/`
2. Install the essentials plugin to `~/.claude/plugins/sisyphus-marketplace/`
3. Update `~/.claude/settings.json` to recognize the marketplace
4. Configure MCP server access

### Manual Setup

If you prefer manual installation:

1. **Install Hooks:**
   ```bash
   cp -r .github/workflows/.claude/hooks ~/.claude/hooks
   ```

2. **Install Plugin:**
   ```bash
   mkdir -p ~/.claude/plugins/sisyphus-marketplace/claude-code-plugins
   cp -r claude-code-plugins/essentials ~/.claude/plugins/sisyphus-marketplace/claude-code-plugins/
   cp .claude-plugin/marketplace.json ~/.claude/plugins/sisyphus-marketplace/
   ```

3. **Update Settings:**
   Add to `~/.claude/settings.json`:
   ```json
   {
     "extraKnownMarketplaces": {
       "sisyphus-marketplace": {
         "source": {
           "type": "local",
           "path": "~/.claude/plugins/sisyphus-marketplace"
         }
       }
     }
   }
   ```

4. **Restart Claude Code**

## Prerequisites

The hooks require:
- **Python 3.12+**
- **uv** - Fast Python package manager
- **Project dependencies** - Run `uv sync` in your project

For hook functionality:
- `ruff` - Linting and formatting
- `basedpyright` - Type checking
- `pytest` - Testing framework

## Usage

### Using Commands

Once installed, you can use slash commands in Claude Code:

```
/execute
```

This loads the execute prompt which instructs Claude to:
- Read and understand ai-todolist.md
- Execute tasks sequentially
- Use subagents for complex work
- Maintain handover documents
- Update task status and completion flags

```
/plan
```

This loads the planning prompt which helps:
- Create detailed work plans
- Break down complex features
- Define clear task boundaries
- Set up verification criteria

### Using Agents

Reference agents in your conversations:

```
@architect please review the implementation of the user authentication system
```

The architect agent will:
- Review code critically
- Check against work plan requirements
- Run tests and quality checks
- Provide detailed feedback

### Understanding Hooks

Hooks run automatically when you use Claude Code:

**Example: anyio enforcement**

If you try to write code using `asyncio` when `anyio` is available:

```python
import asyncio  # ❌ Blocked by hook

async def main():
    await asyncio.sleep(1)  # ❌ Will be rejected
```

The hook will block this and suggest:

```python
import anyio  # ✅ Approved

async def main():
    await anyio.sleep(1)  # ✅ Works
```

**Example: Type checking**

After editing Python files, hooks automatically run:
1. Ruff formatting check
2. Ruff lint check
3. Basedpyright type check
4. Custom opinionated checks (no nested imports, proper __init__.py exports, etc.)

If issues are found, you'll see inline feedback before the tool completes.

## Customization

### Adding Your Own Hooks

1. Create a new Python script in `~/.claude/hooks/`
2. Follow the hook interface:
   ```python
   #!/usr/bin/env python3
   import sys
   import json

   def main():
       # Read hook context from stdin
       context = json.load(sys.stdin)

       # Your logic here

       # Return feedback
       print(json.dumps({
           "approved": True,
           "feedback": "Optional message to Claude"
       }))

   if __name__ == "__main__":
       main()
   ```

3. Update settings.json to register your hook

### Disabling Hooks

To temporarily disable hooks, edit `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [],
    "PostToolUse": [],
    "UserPromptSubmit": []
  }
}
```

Or disable specific hooks by removing them from the arrays.

## Troubleshooting

### "Hook script not found"

Ensure hooks are copied to the correct location:
```bash
ls ~/.claude/hooks/
```

You should see `post_tool_use.py`, `pre-tool-use/`, `post-tool-use/`, etc.

### "uv command not found"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Module not found" in hooks

Run `uv sync` in your project to install dependencies.

### Commands not showing up

1. Check that the marketplace is registered in settings.json
2. Restart Claude Code
3. Verify plugin files are in `~/.claude/plugins/sisyphus-marketplace/`

### Hooks blocking legitimate code

You can bypass a specific hook by:
1. Understanding why it's blocking (read the feedback)
2. Fixing the underlying issue (usually better)
3. Or temporarily disabling the hook in settings.json

## Development

To modify the plugin:

1. Edit files in the repository:
   - `claude-code-plugins/essentials/commands/` - Command prompts
   - `claude-code-plugins/essentials/agents/` - Agent personas
   - `.github/workflows/.claude/hooks/` - Hook scripts

2. Reinstall the plugin:
   ```bash
   python scripts/setup-claude-plugin.py
   ```

3. Restart Claude Code to see changes

## Philosophy

The Sisyphus plugin embodies the project's philosophy:

> "LLM Agents are clever. If the work unit is too long, they subtly ask users things like 'Should I really proceed with the next task?' 'I just completed task X. Should I continue?'"
>
> "Sisyphus is ruthless. If an LLM Agent stops before the work is completely done, Sisyphus forcibly restarts the work every single time."

The hooks and agents are designed to:
- Enforce high code quality standards
- Prevent lazy coding patterns
- Demand accountability for every change
- Keep the boulder rolling until work is truly complete

## Support

For issues with the plugin:
1. Check this documentation
2. Review hook output in Claude Code
3. Open an issue at https://github.com/code-yeongyu/sisyphus/issues

## License

The plugin is distributed under the same license as Sisyphus (Sustainable Use License 1.0).
