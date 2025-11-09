# Migration Guide: v2.1 → v3.0

## Overview

Sisyphus v3.0 introduces a major architectural shift from single-file YAML plans to multi-plan support with dependency management, new directory structure (`.sisyphus/`), and enhanced reference system.

## Breaking Changes

### 1. Directory Structure Reorganization

**Before (v2.1):**
```
project/
├── ai-todolist.yaml       # Single plan file at root
├── notepad.md             # Root level
├── sessions/              # Root level
└── logs/                  # Root level
```

**After (v3.0):**
```
project/
└── .sisyphus/
    ├── tasks/             # Multiple plan YAML files
    │   ├── foundation.yaml
    │   └── main.yaml
    ├── status.json        # Current plan tracking
    ├── notepad.md         # Moved inside
    ├── sessions/          # Moved inside
    └── logs/              # Moved inside
```

**Key Changes:**
- All Sisyphus files now live under `.sisyphus/` directory
- Single `ai-todolist.yaml` → Multiple YAML files in `.sisyphus/tasks/`
- New `status.json` for tracking current active plan across worktrees

### 2. YAML Schema Changes

#### Version Field
```yaml
# v2.1
version: "2.1"

# v3.0
version: "3.0"
```

#### WorkPlan Structure

**Before (v2.1):**
```yaml
version: "2.1"
metadata:
  created_at: "2025-11-01T00:00:00Z"
user_request:
  original: "Build feature X"
  created_at: "2025-11-01T00:00:00Z"
todos:
  - id: "1"
    title: "Task 1"
    status: pending
```

**After (v3.0):**
```yaml
version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: plan-main              # New: Plan ID (required)
    name: "Build feature X"    # New: Plan name
    depends_on: []             # New: Plan dependencies
    todos:
      - id: "1"
        title: "Task 1"
        description: null      # New: Optional description
        status: pending
        children: []           # New: 1-level nesting support
        references: []
        verification_spec: []
    references: []             # Plan-level references
```

**Key Changes:**
- Root `user_request` removed → use `work_plans[].name`
- Root `todos` → `work_plans[].todos` (nested under plan)
- New `work_plans` array: Support multiple plans per file
- New `WorkPlan.id`: Unique identifier for dependency graph
- New `WorkPlan.depends_on`: List of plan IDs this plan depends on
- New `Todo.description`: Optional task description field
- New `Todo.children`: 1-level nested subtasks (children cannot have children)

### 3. Reference System Enhancement

**Before (v2.1):**
```yaml
references:
  - id: "ref-1"
    type: "markdown"
    description: "Documentation"
    content: "Some text"

todos:
  - id: "1"
    references:
      - type: "pointer"
        ref_id: "ref-1"
```

**After (v3.0):**
```yaml
work_plans:
  - id: plan-main
    references:
      - ref_id: "ref-1"        # Pointer to plan-level reference
        uri: "https://..."     # OR direct URI
        inline: null           # OR inline content

    todos:
      - id: "1"
        references:
          - ref_id: "ref-1"           # Reference by ID
          - uri: "file:///path.py"    # Direct URI
          - inline: "Quick note here" # Inline text
```

**Key Changes:**
- `ReferenceItem.type` removed (discriminated by field presence)
- New `ReferenceItem.ref_id`: Points to plan-level reference by ID
- New `ReferenceItem.uri`: Direct URI (file://, https://, etc.)
- New `ReferenceItem.inline`: Inline text content
- **Validation**: `uri` and `inline` are mutually exclusive (only one allowed)
- **Validation**: At least one of `ref_id`, `uri`, or `inline` required

### 4. CLI Command Changes

#### Removed Commands
```bash
# v2.1 - REMOVED in v3.0
sisyphus execute-phase <subcommand>
sisyphus verify-phase <subcommand>
```

#### New Command Structure

**Before (v2.1):**
```bash
sisyphus plan lint --file ai-todolist.yaml
sisyphus plan get task --current
sisyphus execute-phase continue
sisyphus execute-phase bash-verify
```

**After (v3.0):**
```bash
# Plan management
sisyphus plan lint --file .sisyphus/tasks/main.yaml
sisyphus plan overview
sisyphus plan graph --format mermaid
sisyphus plan init --destination .sisyphus/tasks/new.yaml
sisyphus plan export .sisyphus/tasks/main.yaml  # New: YAML → Markdown

# Task execution
sisyphus task show --id 1
sisyphus task current
sisyphus task next
sisyphus task continue

# Verification
sisyphus task verify bash
sisyphus task verify llm mark --evidence "..."
sisyphus task verify manual mark --evidence "..."
sisyphus task verify status
```

#### Command Mapping Table

| v2.1 Command | v3.0 Equivalent |
|--------------|-----------------|
| `plan lint --file <path>` | `plan lint --file <path>` (unchanged) |
| `plan get task --current` | `task current` |
| `plan get task --next` | `task next` |
| `plan get task --id <id>` | `task show --id <id>` |
| `execute-phase continue` | `task continue` |
| `execute-phase bash-verify` | `task verify bash` |
| `execute-phase llm-verify` | `task verify llm mark` |
| `execute-phase manual-verify` | `task verify manual mark` |
| `verify-phase continue` | (merged into `task continue`) |

### 5. Status Tracking

**New in v3.0:** `.sisyphus/status.json`

```json
{
  "version": 1,
  "current_plan": {
    "plan_path": ".sisyphus/tasks/main.yaml",
    "plan_root": ".sisyphus/tasks",
    "updated_at": "2025-11-01T12:34:56.789Z"
  }
}
```

This file tracks:
- Which plan is currently active (for `task continue`)
- Per-worktree state (different git worktrees can work on different plans)
- Auto-updated when switching plans

## Migration Strategy

### Step 1: Backup Existing Files

```bash
# Backup your v2.1 plan
cp ai-todolist.yaml ai-todolist-v2.1-backup.yaml

# Backup other files (optional)
cp -r sessions sessions-backup
cp notepad.md notepad-backup.md
```

### Step 2: Initialize v3.0 Directory Structure

```bash
# Create .sisyphus directory
mkdir -p .sisyphus/tasks

# Move existing files (optional - will be auto-created)
mv notepad.md .sisyphus/notepad.md
mv sessions .sisyphus/sessions
mv logs .sisyphus/logs
```

### Step 3: Convert Your Plan

**Option A: Manual Conversion**

1. Create new v3.0 plan file:

```bash
# Create your first plan
cat > .sisyphus/tasks/main.yaml << 'EOF'
version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: plan-main
    name: "Main Work Plan"
    depends_on: []
    todos: []
    references: []
EOF
```

2. Copy your todos from v2.1:
   - Copy `todos` array from `ai-todolist.yaml`
   - Paste under `work_plans[0].todos`
   - Add `description: null` and `children: []` to each todo if missing

3. Update references:
   - Remove `type` field from all references
   - Change `content` → `inline` for inline text
   - Change `path` → `uri` with `file://` prefix

**Option B: Use Converter Tool (Coming Soon)**

```bash
# Planned for future release
sisyphus plan convert-legacy ai-todolist.yaml --output .sisyphus/tasks/main.yaml
```

### Step 4: Validate Migration

```bash
# Lint the new v3.0 file
sisyphus plan lint --file .sisyphus/tasks/main.yaml

# Check for errors
# Expected: "✓ YAML validation passed. 0 errors."
```

### Step 5: Update Workflows

Update any scripts or documentation that reference old paths:

```bash
# Old
sisyphus plan lint --file ai-todolist.yaml
sisyphus execute-phase continue

# New
sisyphus plan lint --file .sisyphus/tasks/main.yaml
sisyphus task continue
```

### Step 6: Set Active Plan (Optional)

```bash
# Manually create status.json (auto-created by task continue)
cat > .sisyphus/status.json << 'EOF'
{
  "version": 1,
  "current_plan": {
    "plan_path": ".sisyphus/tasks/main.yaml",
    "plan_root": ".sisyphus/tasks",
    "updated_at": "2025-11-01T12:00:00.000Z"
  }
}
EOF
```

## New Features in v3.0

### 1. Multi-Plan Support

Create multiple plans with dependencies:

```yaml
# .sisyphus/tasks/foundation.yaml
version: "3.0"
work_plans:
  - id: plan-foundation
    name: "Foundation Setup"
    depends_on: []
    todos:
      - id: "1"
        title: "Setup infrastructure"
        status: pending

# .sisyphus/tasks/main.yaml
version: "3.0"
work_plans:
  - id: plan-main
    name: "Main Development"
    depends_on: [plan-foundation]  # Waits for foundation to complete
    todos:
      - id: "1"
        title: "Build features"
        status: pending
```

Visualize dependencies:
```bash
sisyphus plan graph --format mermaid
```

### 2. Task Children (1-Level Nesting)

```yaml
todos:
  - id: "1"
    title: "Implement authentication"
    status: in_progress
    children:
      - id: "1.1"
        title: "Add login endpoint"
        status: completed
      - id: "1.2"
        title: "Add logout endpoint"
        status: pending
```

**Note**: Children cannot have nested children (1-level only).

### 3. Inline References

No need to define references globally:

```yaml
todos:
  - id: "1"
    title: "Fix bug"
    references:
      - inline: "User reported this on GitHub issue #123"
      - uri: "https://github.com/org/repo/issues/123"
```

### 4. Dependency Graph Validation

```bash
# Automatically detects circular dependencies
sisyphus plan lint --file .sisyphus/tasks/

# Output:
# ✗ Circular dependency detected: plan-a → plan-b → plan-a
```

### 5. Worktree-Aware Status

Different git worktrees can work on different plans simultaneously:

```bash
# Worktree 1
cd ~/project/main-worktree
sisyphus task continue  # Works on plan-main

# Worktree 2
cd ~/project/feature-worktree
sisyphus task continue  # Can work on plan-feature
```

Status tracked independently per worktree via `status.json`.

## Migration Checklist

- [ ] Backup `ai-todolist.yaml` to `ai-todolist-v2.1-backup.yaml`
- [ ] Create `.sisyphus/tasks/` directory
- [ ] Convert plan to v3.0 format (manual or tool)
- [ ] Change `version: "2.1"` → `version: "3.0"`
- [ ] Wrap todos in `work_plans` array with `id` and `name`
- [ ] Add `depends_on: []` to each work plan
- [ ] Add `description: null` to todos (if missing)
- [ ] Add `children: []` to todos (if missing)
- [ ] Update references: remove `type`, add `ref_id`/`uri`/`inline`
- [ ] Update CLI commands: `execute-phase` → `task`
- [ ] Validate with `sisyphus plan lint`
- [ ] Test with `sisyphus task current`
- [ ] Update CI/CD scripts to use new commands
- [ ] Add `.sisyphus/status.json` to `.gitignore` (if team doesn't share state)

## Common Migration Issues

### Issue 1: "Version 2.1 not supported"

**Error:**
```
UnsupportedPlanVersionError: Plan version 2.1 is not supported.
Please use 'sisyphus plan convert-legacy' to migrate to v3.0
```

**Solution:**
- You're loading a v2.1 file with v3.0 loader
- Update the file to v3.0 format (see Step 3)
- Change `version: "2.1"` → `version: "3.0"`

### Issue 2: "work_plans field required"

**Error:**
```
ValidationError: field required (type=value_error.missing)
  work_plans
```

**Solution:**
- v3.0 requires `work_plans` array at root level
- Wrap your todos in a work plan:

```yaml
work_plans:
  - id: plan-main
    name: "My Plan"
    depends_on: []
    todos: [...]  # Your existing todos here
```

### Issue 3: "uri and inline are mutually exclusive"

**Error:**
```
ValueError: uri와 inline은 동시에 사용할 수 없습니다
```

**Solution:**
- Each reference can have ONLY ONE of: `uri` OR `inline`
- Choose one:

```yaml
# Good
references:
  - uri: "https://example.com"
  - inline: "Some text"

# Bad
references:
  - uri: "https://example.com"
    inline: "Some text"  # ❌ Cannot have both
```

### Issue 4: "Command not found: execute-phase"

**Error:**
```
No such command 'execute-phase'
```

**Solution:**
- `execute-phase` was removed in v3.0
- Use `task` commands instead:
  - `execute-phase continue` → `task continue`
  - `execute-phase bash-verify` → `task verify bash`

### Issue 5: "File not found: ai-todolist.yaml"

**Error:**
```
FileNotFoundError: ai-todolist.yaml
```

**Solution:**
- v3.0 looks for plans in `.sisyphus/tasks/`
- Specify full path:

```bash
sisyphus plan lint --file .sisyphus/tasks/main.yaml
```

Or use `task` commands which auto-resolve from `status.json`:

```bash
sisyphus task current  # No path needed
```

## Example: Complete Before/After

### Before (v2.1)

**File: `ai-todolist.yaml`**

```yaml
version: "2.1"
metadata:
  created_at: "2025-11-01T00:00:00Z"
user_request:
  original: "Build authentication system"
  created_at: "2025-11-01T00:00:00Z"
todos:
  - id: "1"
    title: "Implement login"
    status: pending
    created_at: "2025-11-01T00:00:00Z"
    updated_at: "2025-11-01T00:00:00Z"
    verification_spec:
      - id: "v1"
        title: "Test login"
        description: "Run integration tests"
        verified: false
        verified_at: null
        verification_evidence: null
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "pytest tests/test_auth.py"
            expected_exit_code: 0
    references:
      - type: "pointer"
        ref_id: "auth-spec"
        notes: "See spec"
references:
  - id: "auth-spec"
    type: "markdown"
    description: "Auth specification"
    content: |
      Authentication must use JWT tokens.
```

### After (v3.0)

**File: `.sisyphus/tasks/auth.yaml`**

```yaml
version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: plan-auth
    name: "Build authentication system"
    depends_on: []
    todos:
      - id: "1"
        title: "Implement login"
        description: null
        status: pending
        children: []
        references:
          - ref_id: "auth-spec"
        verification_spec:
          - type: "bash"
            description: "Run integration tests"
            command: "pytest tests/test_auth.py"
            expected_output: null
    references:
      - ref_id: "auth-spec"
        uri: null
        inline: |
          Authentication must use JWT tokens.
```

**Changes Applied:**
1. ✅ Version: `2.1` → `3.0`
2. ✅ Added `work_plans` wrapper with `id` and `name`
3. ✅ Moved `user_request.original` → `work_plans[0].name`
4. ✅ Added `depends_on: []`
5. ✅ Added `description: null` to todo
6. ✅ Added `children: []` to todo
7. ✅ References: removed `type`, removed `notes`, changed `content` → `inline`
8. ✅ Moved global `references` → `work_plans[0].references`

## Rollback Strategy

If you need to rollback to v2.1:

```bash
# Restore backup
cp ai-todolist-v2.1-backup.yaml ai-todolist.yaml

# Downgrade Sisyphus (if needed)
uv pip install sisyphus==2.1.0
```

**Note**: v3.0 can read v2.1 files but will reject them. Keep backups until migration is stable.

## Support & Resources

- **Schema Documentation**: `docs/plan-schema.md`
- **Linter Reference**: `docs/plan-lint.md`
- **GitHub Issues**: Report migration problems
- **Help Command**: `sisyphus --help`

## FAQ

**Q: Can I use both v2.1 and v3.0 files?**
A: No. v3.0 only loads v3.0 files. Migrate all plans before upgrading.

**Q: Do I need to migrate notepad.md and sessions/?**
A: Optional. v3.0 auto-creates them in `.sisyphus/` if missing.

**Q: Can children have children?**
A: No. Only 1 level of nesting is supported (`todo.children` cannot have `children`).

**Q: What happens to my git history?**
A: Use `sisyphus ignore --both` to exclude `.sisyphus/` from git before migrating.

**Q: Can I split one v2.1 plan into multiple v3.0 plans?**
A: Yes! Create multiple YAML files in `.sisyphus/tasks/` with different plan IDs and use `depends_on` to link them.

## Next Steps

After migration:

1. **Explore multi-plan**: Split large plans into smaller dependent plans
2. **Visualize dependencies**: `sisyphus plan graph --format mermaid`
3. **Use inline references**: No need to define every reference globally
4. **Leverage task children**: Break down complex tasks into subtasks
5. **Try worktree workflows**: Work on multiple plans in parallel

---

**Migration completed?** Run `sisyphus task continue` to verify everything works! 🚀
