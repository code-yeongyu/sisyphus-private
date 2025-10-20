# Plugin Validation Guide

This document provides manual validation steps for the web development plugins in the sisyphus marketplace.

## Prerequisites

- Node.js v16 or higher
- npx available
- Claude Code installed

## Plugin Overview

The sisyphus marketplace now includes two new web development plugins:

1. **basic-web-development**: Playwright browser automation via MCP
2. **svelte-web-development**: Svelte 5 development with official MCP and runes

## Installation Steps

### 1. Install Plugins from Sisyphus Marketplace

In Claude Code, use the plugin marketplace commands:

```bash
# List available marketplaces
/plugin marketplace list

# Add sisyphus marketplace (if not already added)
/plugin marketplace add https://github.com/code-yeongyu/sisyphus

# Install basic-web-development plugin
/plugin install basic-web-development

# Install svelte-web-development plugin
/plugin install svelte-web-development
```

### 2. Verify Plugin Installation

```bash
# List installed plugins
/plugin list

# Expected output should include:
# - basic-web-development (0.1.0)
# - svelte-web-development (0.1.0)
```

## MCP Server Validation

### Playwright MCP Validation

The basic-web-development plugin uses the Playwright MCP server.

**Manual Test:**

```bash
# Test Playwright MCP server runs correctly
npx -y @playwright/mcp@latest

# Expected: Server starts without errors
# Note: The server runs in stdio mode, so it will wait for input
# Press Ctrl+C to exit
```

**In Claude Code:**

Once the plugin is installed, Claude Code should automatically start the Playwright MCP server when needed. You can verify this by:

1. Ask Claude Code: "Can you help me automate a web browser task?"
2. Claude should recognize the Playwright MCP tools are available
3. Try a simple task like: "Navigate to example.com and get the page title"

### Svelte MCP Validation

The svelte-web-development plugin uses the official Svelte MCP server.

**Manual Test:**

```bash
# Test Svelte MCP server runs correctly
npx -y @sveltejs/mcp

# Expected: Server starts without errors
# Press Ctrl+C to exit
```

**In Claude Code:**

1. Ask Claude Code: "What are Svelte 5 runes?"
2. Claude should use the Svelte MCP to provide accurate, up-to-date information
3. Try asking: "Show me an example of using $state in Svelte 5"

## Skill Validation

### basic-web-development Skills

The plugin includes two skills:

1. **browser-automation**: Playwright automation patterns
2. **web-testing**: Web testing with Playwright

**Validation Steps:**

1. Create a new file or ask Claude Code to help with browser automation
2. Claude should invoke the `browser-automation` skill when appropriate
3. Verify Claude provides patterns like:
   - Navigation patterns
   - Form filling
   - Data extraction
   - Element interaction

4. Ask about testing: "How do I write Playwright tests?"
5. Claude should invoke the `web-testing` skill
6. Verify Claude provides:
   - Test structure patterns
   - Assertion examples
   - Mocking strategies
   - Best practices

### svelte-web-development Skills

The plugin includes two skills:

1. **svelte5-runes**: Svelte 5 runes system
2. **svelte-patterns**: Common patterns and best practices

**Validation Steps:**

1. Ask Claude Code: "How do I use $state in Svelte 5?"
2. Claude should invoke the `svelte5-runes` skill
3. Verify Claude provides:
   - $state usage examples
   - $derived examples
   - $effect examples
   - Migration guidance

4. Ask: "What are common mistakes in Svelte development?"
5. Claude should invoke the `svelte-patterns` skill
6. Verify Claude provides:
   - Component patterns
   - Common mistakes to avoid
   - Best practices
   - Migration tips

## Expected Behavior

### For basic-web-development Plugin

When you ask Claude Code to help with:
- Browser automation
- Web scraping
- E2E testing
- Form automation

Claude should:
1. Use the Playwright MCP tools for actual browser operations
2. Reference the browser-automation skill for patterns
3. Reference the web-testing skill for testing scenarios
4. Provide code examples that follow Playwright best practices

### For svelte-web-development Plugin

When you ask Claude Code to help with:
- Svelte 5 development
- Reactive state management
- Component patterns

Claude should:
1. Use the Svelte MCP for documentation lookups
2. Reference the svelte5-runes skill for runes usage
3. Reference the svelte-patterns skill for best practices
4. Provide Svelte 5 syntax (not Svelte 4)

## Troubleshooting

### MCP Server Not Loading

**Issue**: Claude Code doesn't recognize Playwright or Svelte MCP tools

**Solutions**:
1. Verify Node.js version: `node --version` (must be v16+)
2. Verify npx is available: `npx --version`
3. Restart Claude Code
4. Check plugin installation: `/plugin list`
5. Manually test MCP server: `npx -y @playwright/mcp@latest`

### Skills Not Invoking

**Issue**: Claude Code doesn't use the skills when expected

**Solutions**:
1. Verify skills are present in plugin directory:
   ```bash
   ls claude-code-plugins/basic-web-development/skills/
   ls claude-code-plugins/svelte-web-development/skills/
   ```
2. Check SKILL.md YAML frontmatter is valid
3. Restart Claude Code
4. Be more explicit in your request (mention "Playwright" or "Svelte 5")

### npx Permission Issues

**Issue**: npx fails to run MCP servers

**Solutions**:
1. Check npm permissions
2. Try with sudo (not recommended for production)
3. Use nvm to manage Node.js versions
4. Clear npm cache: `npm cache clean --force`

## File Structure Verification

Verify the plugin files are correctly structured:

```bash
# basic-web-development structure
ls -R claude-code-plugins/basic-web-development/
# Expected:
# plugin.json
# .mcp.json
# skills/browser-automation/SKILL.md
# skills/web-testing/SKILL.md

# svelte-web-development structure
ls -R claude-code-plugins/svelte-web-development/
# Expected:
# plugin.json
# .mcp.json
# skills/svelte5-runes/SKILL.md
# skills/svelte-patterns/SKILL.md
```

## Validation Checklist

- [ ] Node.js v16+ installed
- [ ] npx available
- [ ] basic-web-development plugin installed
- [ ] svelte-web-development plugin installed
- [ ] Playwright MCP server can start manually
- [ ] Svelte MCP server can start manually
- [ ] Claude Code recognizes Playwright MCP tools
- [ ] Claude Code recognizes Svelte MCP tools
- [ ] browser-automation skill invokes correctly
- [ ] web-testing skill invokes correctly
- [ ] svelte5-runes skill invokes correctly
- [ ] svelte-patterns skill invokes correctly
- [ ] Plugins appear in `/plugin list`
- [ ] All SKILL.md files have valid YAML frontmatter
- [ ] All JSON files are valid

## Additional Resources

- Playwright MCP: https://github.com/microsoft/playwright-mcp
- Svelte MCP: https://github.com/sveltejs/mcp
- Svelte 5 Documentation: https://svelte.dev/docs/svelte/llms.txt
- Claude Code Plugin Documentation: https://docs.claude.com/claude-code

## Support

If you encounter issues not covered in this guide:

1. Check the plugin JSON files for syntax errors
2. Verify the SKILL.md YAML frontmatter format
3. Check Claude Code logs
4. Ensure marketplace.json includes both plugins
5. Try reinstalling the plugins

## Success Indicators

You'll know the plugins are working correctly when:

1. Claude Code automatically suggests using Playwright for browser automation tasks
2. Claude Code provides Svelte 5 syntax (with runes) instead of Svelte 4
3. MCP tools appear in Claude Code's available tools
4. Skills provide relevant, detailed examples
5. Code suggestions follow the patterns documented in SKILL.md files
