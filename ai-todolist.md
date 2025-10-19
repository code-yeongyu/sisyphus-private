# User's Initial Request (For Record)

search of claude code plugin/marketplace docs and references,
please write me new plugin, other than current 'essentials' plugin,
- basic-web-development
	- that has microsoft's playwright as mcp
- svelte web development
	- that has svelte official mcp
	- skills as about the new rune thing and svelte 5 thing (they have llms txt thing so take them as references and skills.md to have common patterns & mistakes)

Validate using tmux cli, actually execute claude code cli to actually mcp is loaded and working

## Additional User Requests (For Record)
@sisyphus-dev-ai please make this as work plan

# Work Objectives

1. Create `basic-web-development` Claude Code plugin with Playwright MCP integration
2. Create `svelte-web-development` Claude Code plugin with official Svelte MCP integration and Svelte 5 runes knowledge
3. Validate both plugins work correctly using tmux CLI with actual Claude Code execution
4. Ensure plugins follow the established sisyphus marketplace structure and conventions

# Work Background

The sisyphus project currently has an `essentials` plugin that provides core functionality for work planning and execution. The user wants to expand the plugin ecosystem with two new web development-focused plugins:

**Current State:**
- ✅ Existing marketplace structure at `.claude-plugin/marketplace.json`
- ✅ Existing `essentials` plugin as reference implementation
- ✅ Claude Code plugin system supports MCP servers, commands, agents, and skills
- ✅ Playwright MCP available as `@playwright/mcp` (official Microsoft package)
- ✅ Svelte MCP available as `@sveltejs/mcp` (official Svelte package)
- ✅ Svelte 5 documentation available in llms.txt format
- ❌ No web development plugins yet

**Needs:**
1. **basic-web-development plugin**: For general web development tasks with browser automation via Playwright MCP
2. **svelte-web-development plugin**: For Svelte 5 development with official MCP, runes documentation, and common patterns/mistakes as skills

**Validation Requirements:**
- Must verify MCP servers load correctly
- Must test actual functionality using tmux CLI
- Must run Claude Code CLI to confirm integration works

# Execution Started
is_execution_started = FALSE

# All Goals Accomplished
is_all_goals_accomplished = FALSE

# Parallel Execution Requested
parallel_requested = FALSE

# Detail Level
detail_level = detailed

# Current Work In Progress
- Work has not started yet.
   - When work begins, change `is_execution_started` above to TRUE.
   - DO NOT start work until the user explicitly says "start the work" or equivalent.
   - **Even if plan reviewer gives OKAY, DO NOT start work**
   - DO NOT start work until the user explicitly says "start the work" or equivalent.

# Required Background Knowledge

## Claude Code Plugin System
- **Plugin Structure**: `.claude-plugin/plugin.json` contains metadata
- **Optional Directories**: `commands/`, `agents/`, `skills/`, `hooks/`
- **MCP Configuration**: `.mcp.json` file configures Model Context Protocol servers
- **Marketplace Format**: `.claude-plugin/marketplace.json` lists all available plugins

## SKILL.md Format (CRITICAL)
Every skill consists of a directory containing a SKILL.md file with:

**Required YAML Frontmatter:**
\`\`\`yaml
---
name: skill-name
description: Short description (200 chars max) - Claude uses this to decide when to invoke
---
\`\`\`

**Content Structure:**
- Main instructions for Claude after frontmatter
- Can reference additional files (REFERENCE.md, scripts/, etc.)
- Target length: 200-500 lines for comprehensive skills

**Example SKILL.md:**
\`\`\`markdown
---
name: browser-automation
description: Common Playwright automation patterns for web testing and scraping
---

# Browser Automation with Playwright MCP

This skill provides patterns for browser automation using the Playwright MCP server.

## Navigation
[Instructions and examples]

## Form Filling
[Instructions and examples]
\`\`\`

## MCP (Model Context Protocol)
- **Purpose**: Standardizes how applications provide context to LLMs
- **Server Types**: stdio-based servers run as subprocesses
- **Configuration Format**: JSON with `command` and `args` fields
- **Common Pattern**: Use `npx` to run MCP servers without installation

## Playwright MCP
- **Package**: `@playwright/mcp` (official Microsoft)
- **Capabilities**: Browser automation via accessibility tree (not screenshots)
- **Use Cases**: Navigation, form-filling, data extraction, testing
- **Installation**: `npx @playwright/mcp@latest`
- **GitHub**: https://github.com/microsoft/playwright-mcp

## Svelte MCP
- **Package**: `@sveltejs/mcp` (official Svelte team)
- **Capabilities**: Svelte 5 documentation, code analysis, best practices
- **Installation**: `npx @sveltejs/mcp`
- **Documentation**: Provides llms.txt format docs for runes
- **GitHub**: https://github.com/sveltejs/mcp

## Svelte 5 Runes
- **What Are Runes**: Symbols that control the Svelte compiler (new in Svelte 5)
- **Key Runes**: `$state`, `$derived`, `$derived.by`, `$effect`
- **llms.txt**: Official documentation at https://svelte.dev/docs/svelte/llms.txt
- **Purpose**: Reactive state management, derived values, side effects

## File Structure and Roles

### Existing Files to Reference FIRST
- `.claude-plugin/marketplace.json`: Marketplace catalog - READ to understand plugin entry format
- `claude-code-plugins/essentials/plugin.json`: Example metadata - READ to understand required fields
- `claude-code-plugins/essentials/.mcp.json`: Example MCP config - READ to understand JSON structure

### New Files to Create
- `claude-code-plugins/basic-web-development/plugin.json`: Plugin metadata
- `claude-code-plugins/basic-web-development/.mcp.json`: Playwright MCP config
- `claude-code-plugins/basic-web-development/skills/browser-automation/SKILL.md`: ~300 lines
- `claude-code-plugins/basic-web-development/skills/web-testing/SKILL.md`: ~250 lines
- `claude-code-plugins/svelte-web-development/plugin.json`: Plugin metadata
- `claude-code-plugins/svelte-web-development/.mcp.json`: Svelte MCP config
- `claude-code-plugins/svelte-web-development/skills/svelte5-runes/SKILL.md`: ~400 lines
- `claude-code-plugins/svelte-web-development/skills/svelte-patterns/SKILL.md`: ~350 lines

# Work Plan

## PRDs & Structures

\`\`\`mermaid
graph TB
    MP[Sisyphus Marketplace<br/>.claude-plugin/marketplace.json] --> ESS[essentials plugin<br/>Already exists]
    MP --> BWD[basic-web-development plugin<br/>NEW]
    MP --> SWD[svelte-web-development plugin<br/>NEW]

    BWD --> BWD_META[plugin.json<br/>Metadata]
    BWD --> BWD_MCP[.mcp.json<br/>Playwright MCP]
    BWD --> BWD_SKILLS[skills/<br/>2 SKILL.md files]

    SWD --> SWD_META[plugin.json<br/>Metadata]
    SWD --> SWD_MCP[.mcp.json<br/>Svelte MCP]
    SWD --> SWD_SKILLS[skills/<br/>2 SKILL.md files]

    BWD_MCP -.->|npx| PLAY[@playwright/mcp<br/>Browser automation]
    SWD_MCP -.->|npx| SVELTE[@sveltejs/mcp<br/>Svelte docs & analysis]
\`\`\`

## Implementation Details

### Pre-Flight Checks (BEFORE starting tasks)
1. Verify Node.js installed: `node --version` (need v16+)
2. Verify npx available: `npx --version`
3. Verify directory structure: `claude-code-plugins/` exists
4. Read reference files from essentials plugin

### basic-web-development Plugin

**Purpose**: General web development with browser automation capabilities

**Components**:
1. `plugin.json`: Standard metadata (see essentials for format)
2. `.mcp.json`: Playwright MCP stdio configuration
3. `skills/browser-automation/SKILL.md`: ~300 lines
   - Frontmatter with name/description
   - Sections: Navigation, Form Filling, Data Extraction, Element Interaction
   - 3-5 code examples per section
   - Focus on accessibility tree usage (not screenshots)
4. `skills/web-testing/SKILL.md`: ~250 lines
   - Frontmatter with name/description
   - Sections: Test Structure, Assertions, Mocking, Best Practices
   - 3-4 code examples per section

**MCP Configuration** (.mcp.json):
\`\`\`json
{
  "playwright": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@playwright/mcp@latest"]
  }
}
\`\`\`

### svelte-web-development Plugin

**Purpose**: Svelte 5 development with runes, official MCP, and best practices

**Components**:
1. `plugin.json`: Svelte-focused metadata
2. `.mcp.json`: Svelte MCP stdio configuration
3. `skills/svelte5-runes/SKILL.md`: ~400 lines
   - Frontmatter with name/description
   - Fetch content from https://svelte.dev/docs/svelte/llms.txt for reference
   - Sections: $state, $derived, $derived.by, $effect, Migration from Svelte 4
   - 4-6 code examples per rune type
   - Include REFERENCE.md link to full llms.txt content
4. `skills/svelte-patterns/SKILL.md`: ~350 lines
   - Frontmatter with name/description
   - Sections: Component Patterns, Common Mistakes, Best Practices, Migration Tips
   - 5-7 code examples showing correct vs incorrect patterns
   - Based on Svelte community patterns

**MCP Configuration** (.mcp.json):
\`\`\`json
{
  "svelte": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@sveltejs/mcp"]
  }
}
\`\`\`

### Validation Strategy

**Commands to use in tmux:**
\`\`\`bash
# If Claude Code CLI available:
claude-code --version                    # Check CLI exists
claude-code /plugin marketplace list     # List available marketplaces
claude-code /plugin list                 # List installed plugins

# For MCP validation (if possible in CLI):
# Check MCP tools loaded - exact command depends on CLI capabilities
\`\`\`

**Manual validation steps if CLI unavailable:**
1. Document marketplace.json structure is valid JSON
2. Document all SKILL.md files have valid YAML frontmatter
3. Document file structure matches expected pattern
4. Create VALIDATION.md with manual test steps for users

## Project Commit Message Style

Based on git log analysis:
- Format: Simple descriptive messages
- Example: "ai-todolist.md as a comment"
- For this work:
  - "feat: add basic-web-development plugin with Playwright MCP"
  - "feat: add svelte-web-development plugin with Svelte 5 MCP and runes"
  - "docs: update marketplace with web development plugins"
  - "test: add validation documentation for plugins"

# TODOs

- [ ] 0. Pre-flight checks and reference reading
   - [ ] 0.1 Verify Node.js installed
      \`\`\`bash
      node --version  # Should be v16 or higher
      npx --version   # Should exist
      \`\`\`
   - [ ] 0.2 Verify project structure
      \`\`\`bash
      ls -la claude-code-plugins/
      ls -la .claude-plugin/marketplace.json
      \`\`\`
   - [ ] 0.3 Read reference files from essentials plugin
      - Read `claude-code-plugins/essentials/plugin.json` for metadata format
      - Read `claude-code-plugins/essentials/.mcp.json` for MCP config format
      - Read `.claude-plugin/marketplace.json` for plugin entry format
   - [ ] Orchestrator Task 0 Verification
      - [ ] Node.js version >= 16?
      - [ ] npx available?
      - [ ] Reference files read and understood?
      - [ ] Ready to proceed with plugin creation?

- [ ] 1. Create basic-web-development plugin structure and configuration
   - [ ] 1.1 Create plugin directory structure
      \`\`\`bash
      mkdir -p claude-code-plugins/basic-web-development/skills/browser-automation
      mkdir -p claude-code-plugins/basic-web-development/skills/web-testing
      \`\`\`
   - [ ] 1.2 Create `plugin.json` based on essentials plugin format
      \`\`\`json
      {
        "name": "basic-web-development",
        "version": "0.1.0",
        "description": "Web development tools with Playwright browser automation via MCP",
        "author": {
          "name": "YeonGyu Kim",
          "email": "public.kim.yeon.gyu@gmail.com",
          "url": "https://github.com/code-yeongyu"
        },
        "homepage": "https://github.com/code-yeongyu/sisyphus",
        "repository": "https://github.com/code-yeongyu/sisyphus",
        "license": "Sustainable Use License: https://github.com/code-yeongyu/sisyphus/blob/main/LICENSE.md"
      }
      \`\`\`
   - [ ] 1.3 Create `.mcp.json` with Playwright MCP configuration
      \`\`\`json
      {
        "playwright": {
          "type": "stdio",
          "command": "npx",
          "args": ["-y", "@playwright/mcp@latest"]
        }
      }
      \`\`\`
   - [ ] 1.4 Create `skills/browser-automation/SKILL.md` (~300 lines)
      **Structure:**
      - YAML frontmatter with name and description (required)
      - Section 1: Navigation patterns (50-80 lines, 3 examples)
      - Section 2: Form filling (50-80 lines, 3 examples)
      - Section 3: Data extraction (50-80 lines, 3 examples)
      - Section 4: Element interaction (50-80 lines, 3 examples)
      - Note: Emphasize accessibility tree usage, not screenshots
   - [ ] 1.5 Create `skills/web-testing/SKILL.md` (~250 lines)
      **Structure:**
      - YAML frontmatter with name and description (required)
      - Section 1: Test structure (60-70 lines, 3 examples)
      - Section 2: Assertions (50-60 lines, 3 examples)
      - Section 3: Mocking (50-60 lines, 2 examples)
      - Section 4: Best practices (40-60 lines, 2 examples)
   - [ ] 1.6 Validate JSON files
      \`\`\`bash
      python -m json.tool claude-code-plugins/basic-web-development/plugin.json > /dev/null && echo "plugin.json valid"
      python -m json.tool claude-code-plugins/basic-web-development/.mcp.json > /dev/null && echo ".mcp.json valid"
      \`\`\`
   - [ ] 1.7 Validate SKILL.md YAML frontmatter
      \`\`\`bash
      # Check first 5 lines contain --- markers and name/description
      head -5 claude-code-plugins/basic-web-development/skills/browser-automation/SKILL.md
      head -5 claude-code-plugins/basic-web-development/skills/web-testing/SKILL.md
      \`\`\`
   - [ ] 1.8 Commit the basic-web-development plugin
      \`\`\`bash
      git add claude-code-plugins/basic-web-development/
      git commit -m "feat: add basic-web-development plugin with Playwright MCP"
      \`\`\`
   - [ ] Orchestrator Task 1 Verification
      - [ ] Directory structure created correctly?
      - [ ] plugin.json matches essentials format with all required fields?
      - [ ] .mcp.json has valid Playwright MCP stdio configuration?
      - [ ] Both SKILL.md files have YAML frontmatter with name and description?
      - [ ] browser-automation SKILL.md is ~300 lines with 4 sections?
      - [ ] web-testing SKILL.md is ~250 lines with 4 sections?
      - [ ] JSON files validated with python -m json.tool?
      - [ ] Commit created successfully?

- [ ] 2. Create svelte-web-development plugin structure and configuration
   - [ ] 2.1 Create plugin directory structure
      \`\`\`bash
      mkdir -p claude-code-plugins/svelte-web-development/skills/svelte5-runes
      mkdir -p claude-code-plugins/svelte-web-development/skills/svelte-patterns
      \`\`\`
   - [ ] 2.2 Fetch Svelte llms.txt for reference
      \`\`\`bash
      curl -o /tmp/svelte-llms.txt https://svelte.dev/docs/svelte/llms.txt
      # Review content for skills creation
      head -50 /tmp/svelte-llms.txt
      \`\`\`
   - [ ] 2.3 Create `plugin.json` for Svelte
      \`\`\`json
      {
        "name": "svelte-web-development",
        "version": "0.1.0",
        "description": "Svelte 5 development with official MCP, runes, and best practices",
        "author": {
          "name": "YeonGyu Kim",
          "email": "public.kim.yeon.gyu@gmail.com",
          "url": "https://github.com/code-yeongyu"
        },
        "homepage": "https://github.com/code-yeongyu/sisyphus",
        "repository": "https://github.com/code-yeongyu/sisyphus",
        "license": "Sustainable Use License: https://github.com/code-yeongyu/sisyphus/blob/main/LICENSE.md"
      }
      \`\`\`
   - [ ] 2.4 Create `.mcp.json` with Svelte MCP configuration
      \`\`\`json
      {
        "svelte": {
          "type": "stdio",
          "command": "npx",
          "args": ["-y", "@sveltejs/mcp"]
        }
      }
      \`\`\`
   - [ ] 2.5 Create `skills/svelte5-runes/SKILL.md` (~400 lines)
      **Structure:**
      - YAML frontmatter with name and description (required)
      - Introduction to runes (30-40 lines)
      - Section 1: $state rune (70-90 lines, 4 examples)
      - Section 2: $derived rune (70-90 lines, 4 examples)
      - Section 3: $derived.by rune (50-70 lines, 3 examples)
      - Section 4: $effect rune (70-90 lines, 4 examples)
      - Section 5: Migration from Svelte 4 (40-60 lines, 2 examples)
      - Reference: Link to https://svelte.dev/docs/svelte/llms.txt
   - [ ] 2.6 Create `skills/svelte-patterns/SKILL.md` (~350 lines)
      **Structure:**
      - YAML frontmatter with name and description (required)
      - Section 1: Component patterns (80-100 lines, 5 examples)
      - Section 2: Common mistakes (80-100 lines, 5 examples showing wrong vs right)
      - Section 3: Best practices (80-100 lines, 4 examples)
      - Section 4: Migration tips (60-80 lines, 3 examples)
      - Based on Svelte community patterns and llms.txt insights
   - [ ] 2.7 Validate JSON files
      \`\`\`bash
      python -m json.tool claude-code-plugins/svelte-web-development/plugin.json > /dev/null && echo "plugin.json valid"
      python -m json.tool claude-code-plugins/svelte-web-development/.mcp.json > /dev/null && echo ".mcp.json valid"
      \`\`\`
   - [ ] 2.8 Validate SKILL.md YAML frontmatter
      \`\`\`bash
      head -5 claude-code-plugins/svelte-web-development/skills/svelte5-runes/SKILL.md
      head -5 claude-code-plugins/svelte-web-development/skills/svelte-patterns/SKILL.md
      \`\`\`
   - [ ] 2.9 Commit the svelte-web-development plugin
      \`\`\`bash
      git add claude-code-plugins/svelte-web-development/
      git commit -m "feat: add svelte-web-development plugin with Svelte 5 MCP and runes"
      \`\`\`
   - [ ] Orchestrator Task 2 Verification
      - [ ] Directory structure created correctly?
      - [ ] Svelte llms.txt fetched and reviewed?
      - [ ] plugin.json matches essentials format with Svelte-specific description?
      - [ ] .mcp.json has valid Svelte MCP stdio configuration?
      - [ ] Both SKILL.md files have YAML frontmatter with name and description?
      - [ ] svelte5-runes SKILL.md is ~400 lines covering all 4 runes + migration?
      - [ ] svelte-patterns SKILL.md is ~350 lines with patterns and mistakes?
      - [ ] Skills reference https://svelte.dev/docs/svelte/llms.txt?
      - [ ] JSON files validated with python -m json.tool?
      - [ ] Commit created successfully?

- [ ] 3. Update marketplace.json with new plugins
   - [ ] 3.1 Read current marketplace.json to understand structure
      \`\`\`bash
      cat .claude-plugin/marketplace.json
      \`\`\`
   - [ ] 3.2 Update marketplace.json to add both plugins to plugins array
      Add these two entries after the essentials plugin:
      \`\`\`json
      {
        "name": "basic-web-development",
        "source": "./claude-code-plugins/basic-web-development",
        "description": "Web development tools with Playwright browser automation via MCP",
        "version": "0.1.0",
        "author": {
          "name": "YeonGyu Kim",
          "email": "public.kim.yeon.gyu@gmail.com"
        }
      },
      {
        "name": "svelte-web-development",
        "source": "./claude-code-plugins/svelte-web-development",
        "description": "Svelte 5 development with official MCP, runes, and best practices",
        "version": "0.1.0",
        "author": {
          "name": "YeonGyu Kim",
          "email": "public.kim.yeon.gyu@gmail.com"
        }
      }
      \`\`\`
   - [ ] 3.3 Validate updated marketplace.json
      \`\`\`bash
      python -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "marketplace.json valid"
      \`\`\`
   - [ ] 3.4 Commit marketplace update
      \`\`\`bash
      git add .claude-plugin/marketplace.json
      git commit -m "docs: update marketplace with web development plugins"
      \`\`\`
   - [ ] Orchestrator Task 3 Verification
      - [ ] Both new plugins added to marketplace?
      - [ ] Plugin entries have all required fields (name, source, description, version, author)?
      - [ ] marketplace.json is syntactically valid JSON?
      - [ ] Commit created successfully?

- [ ] 4. Validate plugins using tmux CLI (or document manual validation)
   - [ ] 4.1 Check if Claude Code CLI is available
      \`\`\`bash
      which claude-code && echo "Claude Code CLI found" || echo "Claude Code CLI not found - will document manual validation"
      \`\`\`
   - [ ] 4.2 IF Claude Code CLI available: Create tmux session for testing
      \`\`\`bash
      tmux new-session -d -s claude-code-validation 'bash'
      \`\`\`
   - [ ] 4.3 IF Claude Code CLI available: Test basic-web-development plugin
      \`\`\`bash
      # Send commands to tmux session:
      tmux send-keys -t claude-code-validation 'claude-code --version' Enter
      sleep 2
      tmux send-keys -t claude-code-validation 'claude-code /plugin list' Enter
      sleep 2
      # Expected: Should show basic-web-development in list
      \`\`\`
   - [ ] 4.4 IF Claude Code CLI available: Test svelte-web-development plugin
      \`\`\`bash
      tmux send-keys -t claude-code-validation 'claude-code /plugin marketplace list' Enter
      sleep 2
      # Expected: Should show sisyphus-marketplace with both new plugins
      \`\`\`
   - [ ] 4.5 IF Claude Code CLI available: Capture output
      \`\`\`bash
      tmux capture-pane -t claude-code-validation -p > /tmp/plugin-validation-output.txt
      cat /tmp/plugin-validation-output.txt
      \`\`\`
   - [ ] 4.6 IF Claude Code CLI available: Clean up tmux
      \`\`\`bash
      tmux kill-session -t claude-code-validation
      \`\`\`
   - [ ] 4.7 IF Claude Code CLI NOT available: Create VALIDATION.md
      Document manual validation steps:
      - How to install plugins from sisyphus marketplace
      - How to verify MCP servers load (npx commands)
      - How to test each skill is invokable
      - Expected behavior for each plugin
   - [ ] 4.8 Commit validation results or documentation
      \`\`\`bash
      # If validation output exists:
      git add /tmp/plugin-validation-output.txt && mv /tmp/plugin-validation-output.txt docs/plugin-validation.txt
      # OR if VALIDATION.md created:
      git add VALIDATION.md
      git commit -m "test: add validation documentation for plugins"
      \`\`\`
   - [ ] Orchestrator Task 4 Verification
      - [ ] Claude Code CLI availability checked?
      - [ ] If CLI available: Tmux session created and commands executed?
      - [ ] If CLI available: Output captured showing plugins listed?
      - [ ] If CLI unavailable: VALIDATION.md created with comprehensive manual steps?
      - [ ] Validation results or documentation committed?
      - [ ] Tmux session cleaned up (if created)?

- [ ] 5. Final verification and documentation
   - [ ] 5.1 Verify all plugin files created
      \`\`\`bash
      ls -R claude-code-plugins/basic-web-development/
      ls -R claude-code-plugins/svelte-web-development/
      \`\`\`
   - [ ] 5.2 Count SKILL.md lines to verify target lengths
      \`\`\`bash
      wc -l claude-code-plugins/basic-web-development/skills/*/SKILL.md
      wc -l claude-code-plugins/svelte-web-development/skills/*/SKILL.md
      \`\`\`
   - [ ] 5.3 Verify all commits made
      \`\`\`bash
      git log --oneline -5
      \`\`\`
   - [ ] 5.4 Verify git status clean
      \`\`\`bash
      git status
      \`\`\`
   - [ ] 5.5 Create README-PLUGINS.md documentation (if not exists)
      Document:
      - How to install sisyphus marketplace in Claude Code
      - How to install each plugin
      - How to use Playwright MCP (example commands/tools)
      - How to use Svelte MCP (example commands/tools)
      - Example workflows for each plugin
      - Troubleshooting: Node.js version, npx issues, MCP loading errors
   - [ ] 5.6 Commit documentation
      \`\`\`bash
      git add README-PLUGINS.md
      git commit -m "docs: add plugin installation and usage guide"
      \`\`\`
   - [ ] 5.7 Update is_all_goals_accomplished = TRUE
   - [ ] Orchestrator Task 5 Verification
      - [ ] All plugin directories exist with correct structure?
      - [ ] SKILL.md files meet target line counts (browser-automation ~300, web-testing ~250, svelte5-runes ~400, svelte-patterns ~350)?
      - [ ] All commits in git history (4-5 commits expected)?
      - [ ] Git status clean (no uncommitted changes)?
      - [ ] README-PLUGINS.md created with comprehensive documentation?
      - [ ] is_all_goals_accomplished set to TRUE?

# Final Work Verification Checklist

- [ ] 1. Pre-flight Checks
   - [ ] Node.js version >= 16 verified?
   - [ ] npx available?
   - [ ] Reference files from essentials plugin read?

- [ ] 2. Plugin Structure Completeness
   - [ ] basic-web-development plugin.json created matching essentials format?
   - [ ] basic-web-development .mcp.json created with Playwright MCP stdio config?
   - [ ] basic-web-development has 2 skills: browser-automation (~300 lines) and web-testing (~250 lines)?
   - [ ] svelte-web-development plugin.json created matching essentials format?
   - [ ] svelte-web-development .mcp.json created with Svelte MCP stdio config?
   - [ ] svelte-web-development has 2 skills: svelte5-runes (~400 lines) and svelte-patterns (~350 lines)?

- [ ] 3. SKILL.md Format Compliance
   - [ ] All 4 SKILL.md files have YAML frontmatter with --- markers?
   - [ ] All frontmatter includes required 'name' field (max 64 chars)?
   - [ ] All frontmatter includes required 'description' field (max 200 chars)?
   - [ ] Skills content follows specified structure and sections?
   - [ ] Code examples included as specified (3-6 per skill)?

- [ ] 4. MCP Configuration Accuracy
   - [ ] Playwright MCP uses package: \`@playwright/mcp@latest\`?
   - [ ] Svelte MCP uses package: \`@sveltejs/mcp\`?
   - [ ] Both use command: \`npx\` with args: \`["-y", "package-name"]\`?
   - [ ] Both configured as type: \`stdio\`?

- [ ] 5. Skills Content Quality
   - [ ] browser-automation skill covers navigation, forms, extraction, interaction?
   - [ ] web-testing skill covers test structure, assertions, mocking, best practices?
   - [ ] svelte5-runes skill documents all runes: $state, $derived, $derived.by, $effect?
   - [ ] svelte5-runes includes migration section from Svelte 4?
   - [ ] svelte-patterns skill includes component patterns, mistakes, best practices, migration?
   - [ ] Svelte skills reference https://svelte.dev/docs/svelte/llms.txt?
   - [ ] Svelte llms.txt fetched and reviewed before creating skills?

- [ ] 6. Marketplace Integration
   - [ ] marketplace.json includes both new plugins?
   - [ ] Plugin entries have consistent author information?
   - [ ] Plugin versions all set to 0.1.0?
   - [ ] Source paths correct: ./claude-code-plugins/{plugin-name}?
   - [ ] marketplace.json is valid JSON?

- [ ] 7. Validation Completeness
   - [ ] If Claude Code CLI available: Validation executed via tmux?
   - [ ] If Claude Code CLI unavailable: VALIDATION.md created with manual steps?
   - [ ] MCP server loading approach documented?
   - [ ] Validation results or manual test plan committed?

- [ ] 8. Git Commit Quality
   - [ ] Pre-flight/reference reading not committed (preparation only)?
   - [ ] basic-web-development plugin committed separately?
   - [ ] svelte-web-development plugin committed separately?
   - [ ] Marketplace update committed separately?
   - [ ] Validation documentation committed?
   - [ ] README-PLUGINS.md committed?
   - [ ] Commit messages follow project conventions?
   - [ ] Git status clean (no uncommitted changes)?

- [ ] 9. Documentation Completeness
   - [ ] README-PLUGINS.md includes installation instructions?
   - [ ] README-PLUGINS.md includes usage examples for both plugins?
   - [ ] MCP requirements documented (Node.js, npx)?
   - [ ] Troubleshooting section included?
   - [ ] Example workflows provided?

- [ ] 10. Error Handling & Edge Cases
   - [ ] Plan accounts for Claude Code CLI not being available?
   - [ ] Plan includes fallback to manual validation documentation?
   - [ ] JSON validation steps included for all JSON files?
   - [ ] YAML frontmatter validation steps included?
   - [ ] Pre-flight checks prevent starting with missing dependencies?
