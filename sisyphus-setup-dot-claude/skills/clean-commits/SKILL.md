---
name: clean-commits
description: Automatically clean up and organize git commit history using git absorb and autosquash rebase. Activate when user requests commit cleanup, history organization, or mentions phrases like "clean up commits", "organize my commits", "fix commit history", "tidy up commits", "clean commits", "absorb changes", "fixup commits", "squash commits properly", "rebase and clean", "prepare commits for PR", "make commits cleaner", or "integrate scattered changes". Stages all changes, absorbs them into appropriate existing commits, creates fixup commits for remaining changes, and performs autosquash rebase with autoStash and rerere enabled for a polished commit history.
---

# Clean Commits

Automatically organize and clean up git commits by intelligently integrating changes into existing commits using `git absorb` and creating fixup commits for remaining changes.

## Overview

This skill automates the tedious process of maintaining a clean git history by:
- Staging all changes
- Running `git absorb --and-rebase` to automatically integrate changes into appropriate existing commits
- Creating `fixup` commits for changes that couldn't be absorbed
- Performing autosquash rebase with `autoStash` and `rerere` enabled

The workflow ensures a clean, logical commit history without manual interactive rebasing.

## When to Use

Activate this skill when the user:
- Wants to clean up messy commit history
- Has scattered changes that should be integrated into existing commits
- Needs to prepare commits for a pull request
- Mentions phrases like:
  - "clean my commits"
  - "organize commit history"
  - "absorb my changes"
  - "fix up commits"
  - "make commits cleaner"

## Workflow

### Step 1: Invoke the Script

Run the clean commits script:

```bash
~/.claude/skills/clean-commits/scripts/clean_commits.py [BASE_BRANCH]
```

**Parameters:**
- `BASE_BRANCH` (optional): The base branch to rebase onto
  - If not provided, automatically detects using `~/other/updatebranch` or common branches (main/master/develop/dev)
  - If auto-detection fails, prompts the user for input

**Options:**
- `-f, --force`: Force rebase even with conflicts

**Example usage:**
```bash
# Auto-detect base branch
./clean_commits.py

# Specify base branch explicitly
./clean_commits.py main

# Force mode
./clean_commits.py -f main
```

### Step 2: Automatic Process

The script automatically executes the following sequence:

1. **Stage Changes**
   ```bash
   git add .
   ```

2. **Run git absorb with rebase**
   ```bash
   git absorb --and-rebase [--force] \
     -c rebase.autosquash=true \
     -c rebase.autoStash=true \
     -c rerere.enabled=true \
     BASE_BRANCH
   ```

3. **Check for Remaining Changes**
   - If changes remain after absorb, proceed to fixup creation
   - If no changes remain, workflow completes

4. **Create Fixup Commits** (if needed)
   - For each modified file:
     - Find the most recent commit that modified the file
     - Stage the file
     - Create a fixup commit: `git commit --fixup <commit-hash>`

5. **Run Autosquash Rebase** (if fixup commits were created)
   ```bash
   git rebase -i --autosquash \
     -c rebase.autoStash=true \
     -c rerere.enabled=true \
     BASE_BRANCH
   ```

6. **Verify Clean State**
   - Check if any uncommitted changes remain
   - Report completion status to user

### Step 3: Handle Results

The script provides clear feedback:

**Success:**
```
✓ All commits cleaned successfully
Rebased onto: main
```

**Partial Success:**
```
⚠ Some changes could not be automatically committed
Please review and commit manually
```

## Base Branch Detection Logic

The script uses the following priority order to detect the base branch:

1. **User-provided argument**: If explicitly specified, use that branch
2. **updatebranch script**: Check `~/other/updatebranch --detect-base`
3. **Common branches**: Search for `main`, `master`, `develop`, or `dev`
4. **User prompt**: Ask user to enter base branch name

This ensures maximum flexibility while minimizing manual input.

## Git Configuration

The workflow automatically applies these git configurations during rebase operations:

- `rebase.autosquash=true`: Automatically rearrange fixup commits
- `rebase.autoStash=true`: Automatically stash and pop changes before/after rebase
- `rerere.enabled=true`: Reuse recorded resolution of conflicted merges

These settings are applied temporarily via `-c` flags and don't modify global git config.

## Requirements

**System dependencies:**
- `git` (with `git absorb` installed)
- `uv` (for running the Python script)

**Install git absorb:**
```bash
# macOS
brew install git-absorb

# Linux
cargo install git-absorb
```

## Error Handling

The script handles common scenarios:

- **No base branch detected**: Prompts user for input
- **git absorb warnings**: Displays warnings but continues
- **Fixup target not found**: Skips file and reports to user
- **Rebase conflicts**: Follows standard git rebase conflict resolution

## Advanced Usage

### Force Mode

Use force mode when you want to override git absorb's safety checks:

```bash
./clean_commits.py -f
```

**Warning**: Force mode can potentially lose uncommitted changes. Use with caution.

### Custom Base Branch

Explicitly specify a base branch for non-standard workflows:

```bash
./clean_commits.py feature/parent-branch
```

## Best Practices

1. **Review changes before running**: Use `git status` and `git diff` to understand what will be absorbed
2. **Commit related changes together**: Group related modifications before running the script
3. **Test after cleaning**: Verify your changes still work correctly after commit reorganization
4. **Communicate with team**: If working on a shared branch, coordinate before force-pushing cleaned history

## Troubleshooting

**Issue**: Script can't find base branch
- **Solution**: Explicitly provide base branch as argument

**Issue**: Changes not absorbed into commits
- **Solution**: Ensure your changes modify lines that exist in recent commits

**Issue**: Fixup commits not squashing
- **Solution**: Verify `git rebase -i --autosquash` is running correctly and no conflicts exist

**Issue**: Rebase conflicts
- **Solution**: Resolve conflicts manually using standard git rebase conflict resolution

## Resources

### scripts/clean_commits.py

The main executable Python script that orchestrates the entire workflow. It uses:
- **typer**: CLI argument parsing and user interaction
- **rich**: Beautiful terminal output with progress bars and panels
- **asyncio**: Asynchronous subprocess execution for git commands

The script is self-contained with PEP 723 inline dependencies and can be run directly without installing dependencies globally.
