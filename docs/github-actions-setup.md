# GitHub Actions Setup Guide

This guide explains how to ensure your GitHub Actions workflows have the necessary Sisyphus Claude Code plugins installed.

## Issue

The `claude-core.yml` workflow (triggered by `@claude` mentions) was missing the essential Sisyphus plugin installation steps that are present in the `issue-as-sisyphus-work.yml` workflow.

## Required Plugin Setup

All workflows that use Claude Code should include the following steps to install the Sisyphus essential plugin:

### 1. Install Claude Code CLI

```yaml
- name: Install Claude Code
  run: |
    curl -fsSL https://claude.ai/install.sh | bash
    echo "$HOME/.local/bin" >> $GITHUB_PATH
```

### 2. Ensure Claude Code in PATH

```yaml
- name: Ensure Claude Code in PATH
  run: |
    echo "$HOME/.local/bin" >> $GITHUB_PATH
    export PATH="$HOME/.local/bin:$PATH"
    # Verify claude is accessible
    claude --version || echo "Claude command failed!"
```

### 3. Setup Sisyphus Claude Code Plugin

```yaml
- name: Setup Sisyphus Claude Code Plugin
  run: |
    claude plugin marketplace add ./
    claude plugin install essentials@sisyphus-marketplace
```

## Workflow Integration

These steps should be added:

1. **After**: Setting up Bun and Node
2. **Before**: Running the Claude Code action

### Example Workflow Structure

```yaml
steps:
  # ... checkout, setup node, setup bun ...

  - name: Get Bun Path to use
    id: bun_path
    run: |
      BUN_PATH=$(which bun)
      echo "BUN_PATH=$BUN_PATH" >> $GITHUB_OUTPUT

  # ✅ ADD THESE STEPS HERE
  - name: Install Claude Code
    run: |
      curl -fsSL https://claude.ai/install.sh | bash
      echo "$HOME/.local/bin" >> $GITHUB_PATH

  - name: Ensure Claude Code in PATH
    run: |
      echo "$HOME/.local/bin" >> $GITHUB_PATH
      export PATH="$HOME/.local/bin:$PATH"
      claude --version || echo "Claude command failed!"

  - name: Setup Claude Code configuration
    run: |
      if [ -d ".github/workflows/.claude" ]; then
        mkdir -p ~/.claude
        cp -r .github/workflows/.claude/* ~/.claude/
      fi

  - name: Setup Sisyphus Claude Code Plugin
    run: |
      claude plugin marketplace add ./
      claude plugin install essentials@sisyphus-marketplace
  # ✅ END OF NEW STEPS

  - name: Run Claude Code
    uses: anthropics/claude-code-action@v1.0.13
    # ... rest of configuration
```

## Why This Is Needed

The Sisyphus essential plugin provides:

- Custom slash commands specific to Sisyphus workflows
- Agent definitions (executor, architect, plan-reviewer)
- Project-specific hooks and configurations
- Enhanced tooling for task management

Without these plugins, Claude Code won't have access to Sisyphus-specific functionality when triggered via `@claude` mentions.

## Affected Workflows

Currently, the following workflow needs these steps added:

- `.github/workflows/claude-core.yml` - Main Claude Code workflow for `@claude` mentions

The following workflow already has these steps:

- `.github/workflows/issue-as-sisyphus-work.yml` - Issue-to-work automation

## GitHub App Permissions Note

Note that the Claude Code GitHub App does not have permission to modify workflow files (`.github/workflows/*.yml`) for security reasons. These changes must be made manually by repository maintainers.

For more information, see the [Claude Code Action FAQ](https://github.com/anthropics/claude-code-action/blob/main/docs/faq.md).
