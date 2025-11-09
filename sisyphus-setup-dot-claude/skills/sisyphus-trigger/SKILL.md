---
name: sisyphus-trigger
description: Activate when user expresses intent to start Sisyphus work (e.g., "okay then work like that", "let's execute this", "start working on this"). Extract ai-todolist.md content from GitHub comments/files, create branch, commit, and trigger GitHub Actions workflow. If no ai-todolist format found, load plan-writer skill instead.
---

# Sisyphus Work Trigger

Automate the process of starting Sisyphus work from user's intent, either with existing ai-todolist.md content or by creating a new plan.

## When to Use This Skill

Activate this skill when:
1. User expresses intent to start work with phrases like:
   - "okay then work like that"
   - "let's execute this"
   - "start working on this"
   - Any phrase indicating readiness to begin work
2. **AND** user mentions or references:
   - A GitHub issue/PR comment
   - An existing file path
   - Direct content that might contain ai-todolist.md format

## Workflow Decision Tree

```
User Intent Detected
    |
    v
Search for ai-todolist.md format content
    |
    +-- Found? --> Extract & Trigger Workflow (Step A)
    |
    +-- Not Found? --> Load plan-writer Skill (Step B)
```

---

## Step 0: Register All Steps in TodoWrite

Before proceeding, use the TodoWrite tool to register all upcoming steps as a todo list:

```
Use TodoWrite to create todos for the following:
1. Search for ai-todolist.md format content
2. Extract content from GitHub comments (if ai-todolist found)
3. Verify ai-todolist.md format
4. Generate branch name
5. Create branch and commit
6. Trigger GitHub Actions workflow
7. Inform user of success

Mark each step as 'pending' initially, then update to 'in_progress' and 'completed' as you work through them.
```

This ensures full visibility into the workflow execution and allows for proper task tracking.

---

## Step A: ai-todolist.md Format Found

### 1. Extract Content from GitHub Comments

Use `gh` CLI to extract comments from issues or PRs:

```bash
# Get specific comment by comment ID
gh api /repos/{owner}/{repo}/issues/comments/{comment_id} --jq '.body'

# Get all comments from an issue
gh issue view {issue_number} --json comments --jq '.comments[].body'

# Get all comments from a PR
gh pr view {pr_number} --json comments --jq '.comments[].body'

# Search for comments containing specific text
gh issue view {issue_number} --json comments --jq '.comments[] | select(.body | contains("# TODOs")) | .body'
```

**Example workflow:**
```bash
# If user says "use that comment from PR #123"
gh pr view 123 --json comments --jq '.comments[] | select(.body | contains("# TODOs")) | .body' > ai-todolist.md
```

### 2. Verify ai-todolist.md Format

Check if the content has the required structure (see [example-ai-todolist.md](references/example-ai-todolist.md)):
- Contains `# TODOs` section
- Has `- [ ]` checkbox items
- Has `is_execution_started = FALSE` marker
- Has `is_all_goals_accomplished = FALSE` marker

### 3. Generate Branch Name

Create a descriptive branch name from the task title:
```bash
# Extract task goal and slugify
# Example: "mode integration" -> "sisyphus-dev-ai/mode-integration"
BRANCH_NAME="sisyphus-dev-ai/$(echo '{task_summary}' | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | sed 's/-$//')"
```

Pattern: `sisyphus-dev-ai/{descriptive-name}`

### 4. Create Branch and Commit

```bash
# Create and checkout new branch
git checkout -b "$BRANCH_NAME"

# Reset Sisyphus environment
sisyphus reset --include-task-specs
git add .
git commit -m "sisyphus reset"

# Save ai-todolist.md
# (Content should be saved to ./ai-todolist.md)
git add ai-todolist.md
git commit -m "sisyphus work init"

# Push to remote
git push -u origin "$BRANCH_NAME"
```

### 5. Trigger GitHub Actions Workflow

Use the bundled script:
```bash
bash scripts/trigger_workflow.sh "$BRANCH_NAME"
```

This will execute:
```bash
gh workflow run trigger-sisyphus-work.yml -f branch_name="$BRANCH_NAME"
```

### 6. Inform User

Report back with:
- Branch name created
- Commit SHAs
- GitHub Actions workflow run URL

Example:
```
SUCCESS: Sisyphus work triggered!

* Branch: sisyphus-dev-ai/mode-integration
* Commits:
   - a1b2c3d: sisyphus reset
   - e4f5g6h: sisyphus work init
* Workflow: https://github.com/owner/repo/actions/runs/...

The workflow will:
1. Checkout the branch
2. Run sisyphus work --no-tui
3. Create PR when complete
```

---

## Step B: No ai-todolist.md Format Found

If the referenced content does NOT match ai-todolist.md format:

### 1. Load plan-writer Skill

```
Load the plan-writer skill to create a new work plan.
```

The plan-writer skill will:
- Analyze user requirements
- Generate structured ai-todolist.md
- Support --detail levels (minimal|balanced|detailed|extreme)
- Get plan-reviewer validation

### 2. After Plan Created

Once plan-writer generates ai-todolist.md:
- Return to Step A (Extract & Trigger Workflow)
- Continue with branch creation and workflow trigger

---

## Important Notes

### Branch Naming Convention

Always use `sisyphus-dev-ai/` prefix for automated work branches:
- Pattern: `sisyphus-dev-ai/{descriptive-kebab-case}`
- Keep names concise but descriptive
- Use English words even if task is in Korean

### Commit Message Convention

Use exactly these commit messages:
1. First commit: `"sisyphus reset"`
2. Second commit: `"sisyphus work init"`

### Error Handling

If workflow trigger fails:
- Check GitHub CLI authentication: `gh auth status`
- Verify workflow file exists: `gh workflow list`
- Ensure branch is pushed: `git branch -r | grep sisyphus-dev-ai`

### Workflow Requirements

The `trigger-sisyphus-work.yml` workflow expects:
- Branch name as input parameter
- Existing `ai-todolist.md` in the branch
- Will fail if ai-todolist.md is missing

---

## Reference

See [example-ai-todolist.md](references/example-ai-todolist.md) for the required format structure.
