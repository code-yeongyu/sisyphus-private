# Sisyphus: Natural Language Compiler

In Greek mythology, Sisyphus was condemned to roll a boulder up a hill for eternity as punishment for deceiving the gods. LLM Agents haven't done anything wrong, but they're constantly pushing their limits every day. My life is no different. When I look back, we're all just like them.
Yes, LLM Agents are no different from us humans.
With clear work plans, LLM Agents can produce excellent results. Delegate the work, and humans just need to review when it's done.
If you're an engineer, Sisyphus turns you into a CTO.

Sisyphus aims to compile natural language into code. Install it with:

```sh
uv tool install sisyphus
```

Sisyphus is the orchestrator of LLM Agents. It keeps the boulder rolling until the work is finished.

What Sisyphus does is simple. Sisyphus does two things.

## What is Sisyphus

### Let there be light. And there will be light.

It turns your words into code. Not only simple code, but big code, projects, products.
It creates work plans while communicating with you. It makes everything concrete with no ambiguity.
It communicates with you based on the work plan document, and you can edit it directly.

### From Plans to Products

The plan is complete. Now it's time to compile natural language into code.

```sh
sisyphus work
```

A Textual UI appears. You can watch the agents work. You can send messages in the middle. Press ESC to pause the work.

Sisyphus executes based on the provided work plan.

#### Roll a huge boulder
It calls LLM Agents like Claude Code or OpenCode (experimental support) to progress the work.
The main agent reads the work plan and assigns tasks to sub-agents (Subagents).

##### Executors
Executors are provided with everything they need: what's happening now, what they need to do, and what information is required.
Executors focus on one appropriately-sized task. Clean context. Higher quality. No confusion.

Executors work with sufficient tools. Not just linters, formatters, and type checkers, but also tools (Claude Code Hooks) that demand accountability for every comment written, detect lazy coding patterns, and strongly warn against lazy attempts.
- You can attach your own custom static analyzers to force Sisyphus to write code in your style. Of course, Sisyphus can create these analyzers for you too.

Executors finish their tasks. They evaluate the work, note special considerations, assess quality, and write handover documents for the next executor.
They report completion to the main agent, "I am done. I have completed the task!"

##### Talk is cheap. Show me the code.

The executor says they're done. The agent doesn't trust them. Upon receiving the report, it verifies directly.
It runs test code, actually executes it for verification, and reads the code inside. It reads the handover documents. It's micromanagement.
If the executor actually completed the plan, it moves to the next task. If not, it assigns the task again with the predecessor's mistakes mentioned, telling them not to make such mistakes and to redo the original task properly.

##### No free time allowed.

LLM Agents are clever.
If the work unit is too long, they subtly ask users things like "Should I really proceed with the next task?" "I just completed task X. Should I continue?"

Sisyphus is ruthless.
If an LLM Agent stops before the work is completely done, Sisyphus forcibly restarts the work every single time. The session doesn't stop until the work is truly complete.

##### Boss, I'm Done! I Really Worked Hard!

The LLM Agent finishes the work. Sisyphus reads it.
Sisyphus brings in an outside expert (another LLM Agent with no context). The verification agent.
It reads the work plan. Reads the handover documents. Imagines what it should look like if the work is really done.
The verification agent starts verification.
It examines the code.
It reviews the attached documents.
It runs tests.
It actually uses it. Performs QA.
It tries direct terminal calls, launches debuggers, opens browsers.

The verification agent is disappointed.
It provides very critical and strong feedback.
"This is not what I imagined." "Item A in the plan doesn't even work." "Why did you skip B? You cannot skip what's in the plan."

Sisyphus is ruthless.
It collects this feedback and summons the LLM Agent again.

##### Done

Sisyphus just keeps rolling the boulder.
The work is complete.

---

## Getting Started

### Installation

Sisyphus requires Python 3.12 or higher.

```sh
uv tool install sisyphus-ai
```

Then run following commands to setup environments for sisyphus.

```sh
claude plugin marketplace add code-yeongyu/sisyphus
claude plugin install sisyphus@sisyphus-marketplace
```

After installation, you can run Sisyphus directly:
```sh
sisyphus work
```

### Quick Start

Sisyphus v3.0 uses **WorkPlan YAML files** for structured task management.

#### 1. Initialize a Work Plan

```sh
# Create a new plan template
sisyphus-speckit plan init --destination .sisyphus/tasks/my-project.yaml
```

This creates a v3.0 YAML file with the following structure:

```yaml
version: "3.0"
metadata:
  created_at: "2025-11-02T00:00:00Z"
work_plans:
  - id: plan-main
    name: "My Project Plan"
    depends_on: []  # Optional: list plan IDs this depends on
    todos:
      - id: "1"
        title: "Implement feature X"
        description: "Add user authentication"
        status: pending
        references:
          - inline: "Use JWT tokens for session management"
        verification_spec:
          - type: bash
            description: "Run tests"
            command: "pytest tests/test_auth.py"
```

#### 2. Edit Your Plan

Open `.sisyphus/tasks/my-project.yaml` and customize:
- `todos`: Your task list with IDs, titles, descriptions
- `depends_on`: Plan dependencies (for multi-plan projects)
- `references`: Inline notes or external URLs
- `verification_spec`: Automated checks (bash commands, etc.)

#### 3. Validate Your Plan

```sh
# Check for errors, cycles, missing dependencies
sisyphus-speckit plan lint .sisyphus/tasks/

# Visualize dependency graph
sisyphus-speckit plan graph .sisyphus/tasks/ --format ascii
```

Example graph output:
```
plan-foundation
  └─> plan-main
      └─> plan-testing
```

#### 4. Execute Tasks

```sh
# Start working on tasks with Claude agent
sisyphus-speckit task continue --execute claude:sonnet
```

The TUI appears showing agent progress:
- Live chat log with agent's work
- Current task status
- Real-time verification results

#### 5. Track Progress

```sh
# Show current task
sisyphus-speckit task current

# Show next task
sisyphus-speckit task next

# Export YAML to Markdown for review
sisyphus-speckit plan export .sisyphus/tasks/my-project.yaml
```

---

## Commands

### Plan Management (`sisyphus-speckit plan`)

#### `sisyphus-speckit plan init`

Create a new v3.0 WorkPlan template.

```sh
# Create in default location (.sisyphus/tasks/)
sisyphus-speckit plan init

# Specify custom path
sisyphus-speckit plan init --destination .sisyphus/tasks/feature-auth.yaml
```

#### `sisyphus-speckit plan lint`

Validate YAML structure, dependencies, and references.

```sh
# Lint all plans in directory
sisyphus-speckit plan lint .sisyphus/tasks/

# Lint specific file
sisyphus-speckit plan lint .sisyphus/tasks/my-plan.yaml
```

Checks for:
- Circular dependencies (A depends on B, B depends on A)
- Missing plan files
- Invalid reference IDs
- Malformed YAML structure

#### `sisyphus-speckit plan graph`

Visualize plan dependencies.

```sh
# ASCII format (terminal-friendly)
sisyphus-speckit plan graph .sisyphus/tasks/ --format ascii

# Mermaid format (for documentation)
sisyphus-speckit plan graph .sisyphus/tasks/ --format mermaid

# PNG format (requires graphviz)
sisyphus-speckit plan graph .sisyphus/tasks/ --format png --output graph.png
```

#### `sisyphus-speckit plan export`

Convert YAML to Markdown format (ai-todolist.md style).

```sh
# Output to stdout
sisyphus-speckit plan export .sisyphus/tasks/my-plan.yaml

# Save to file
sisyphus-speckit plan export .sisyphus/tasks/my-plan.yaml --output ai-todolist.md
```

#### `sisyphus-speckit plan overview`

Show summary of all plans and current status.

```sh
sisyphus-speckit plan overview
```

### Task Execution (`sisyphus-speckit task`)

#### `sisyphus-speckit task continue`

Resume or start task execution with agents.

```sh
# Use Claude agent with TUI
sisyphus-speckit task continue --execute claude:sonnet

# CLI mode (no TUI)
sisyphus-speckit task continue --execute claude:sonnet --no-tui
```

#### `sisyphus-speckit task current`

Show the currently active task.

```sh
sisyphus-speckit task current
```

#### `sisyphus-speckit task next`

Show the next pending task.

```sh
sisyphus-speckit task next
```

#### `sisyphus-speckit task show`

Display details of a specific task.

```sh
sisyphus-speckit task show --id 1
```

#### `sisyphus-speckit task verify`

Run verification checks for tasks.

```sh
# Run bash verification commands
sisyphus-speckit task verify bash

# Manual verification status
sisyphus-speckit task verify status
```

### Legacy Support (`sisyphus work`)

The original `sisyphus work` command still works for v2.1 compatibility.

```sh
# Basic execution (Claude + TUI)
sisyphus work

# CLI mode (useful for automation)
sisyphus work --no-tui

# Use OpenCode agent
sisyphus work --agent opencode
```

### Agent Selection

Sisyphus supports two agents.

**Claude**
```sh
# Default model
sisyphus work --agent claude

# Specify model
sisyphus work --agent claude:sonnet

# Adjust SDK options
sisyphus work --agent claude \
  --execute-sdk-options '{"temperature": 0.8}'
```

**OpenCode** (Alpha Support)
```sh
# Auto-start server
sisyphus work --agent opencode

# Use external server
sisyphus work --agent opencode \
  --opencode-server-url http://localhost:8080
```

### Separate Execute and Verify

This is Sisyphus's core feature. You can use different agents for execution and verification.

```sh
# Execute with Claude, verify with OpenCode
sisyphus work \
  --execute claude:sonnet \
  --verify opencode

# Execute only, skip verification
sisyphus work --execute claude
```

The verification agent always starts with a fresh session. Clean context. No bias.

### Prompt Customization

You can change the instructions given to agents.

```sh
# Slash commands (built-in prompts)
sisyphus work \
  --execute-prompt /execute \
  --verify-prompt /architect

# Read from files
sisyphus work \
  --execute-prompt prompts/my-execute.md \
  --verify-prompt prompts/my-verify.md

# Pass as direct text
sisyphus work \
  --execute-prompt "Complete all tasks in ai-todolist.md"

# Append additional instructions
sisyphus work \
  --execute-extra-prompt "Must use type hints" \
  --verify-extra-prompt "Focus on security vulnerabilities"
```

### `sisyphus reset`

Clean up the work environment.

```sh
# Delete only sessions and logs
sisyphus reset

# Delete work plans too (start from scratch)
sisyphus reset --include-task-specs
```

### Managing Sisyphus Files in Existing Projects

When using Sisyphus with existing projects, you may need to manage the files it generates.

#### Adding Files to .gitignore

Use `sisyphus ignore` to automatically add Sisyphus-generated files to your git configuration.

```sh
# Default: Add to .gitignore (shared with team)
sisyphus ignore

# Local-only: Add to .git/info/exclude (not version-controlled)
sisyphus ignore --exclude-only

# Both: Add to both .gitignore and .git/info/exclude
sisyphus ignore --both
```

**What gets ignored:**
- `ai-todolist.md` - Work plan
- `notepad.md` - Work notes
- `sessions/` - Agent session data
- `logs/` - Log files
- `agentloop.json` - Agent state
- `claude_session_*.log` - Session logs

**When to use:**
- **Default `.gitignore`**: When setting up Sisyphus in a shared project
- **`--exclude-only`**: When you only want local ignoring (e.g., on a personal branch)
- **`--both`**: When you want maximum safety (redundant but covers all bases)

#### Cleaning Git History

If Sisyphus files were accidentally committed, use `sisyphus clean-history` to remove them from git history.

```sh
# Show what would be cleaned (safe to run)
sisyphus clean-history --dry-run

# Auto-detect base branch and show cleanup guide
sisyphus clean-history

# Specify base branch manually
sisyphus clean-history --base-branch origin/develop
```

**How it works:**
1. Detects base branch (`origin/main` → `origin/master` → `origin/develop`)
2. Finds commits containing Sisyphus files
3. Generates step-by-step `git rebase -i` instructions
4. Provides exact commands to remove files from each commit

**Important:**
- Protects main/master branches (won't run on them)
- Always shows instructions before making changes
- Use `--dry-run` to preview without modifying
- After cleanup, use `git push --force-with-lease` to sync

**Example output:**
```
⚠ Git History Cleanup Guide

Found 2 commit(s) containing Sisyphus files since origin/main:

1. abc123 - Add feature
   Files: ai-todolist.md, sessions/test.json

2. def456 - Another commit
   Files: logs/test.log

Step-by-step cleanup instructions:
1. Start interactive rebase:
   $ git rebase -i origin/main
...
```

---

## TUI Usage

Textual-based terminal UI.

### Layout

```
┌─────────────────────────────────────┐
│                                     │
│       Chat Log (70%)                │  ← Agent messages, progress
│                                     │
├─────────────────────────────────────┤
│    Status Panel (20%)               │  ← Current stage, task status
├─────────────────────────────────────┤
│ > Input Bar (10%)                   │  ← Message input
└─────────────────────────────────────┘
```

### Keyboard Shortcuts

- **Ctrl+C** - Interrupt work
- **Ctrl+D** - Exit
- **UP** - Edit previous message
- **Shift+Enter** - New line in input bar
- **Enter** - Send message

### Theme

Auto-detects system theme. Manual override available.

```sh
# Auto-detect (default)
sisyphus work --theme system

# Dark mode (Catppuccin Mocha)
sisyphus work --theme mocha

# Light mode (Catppuccin Latte)
sisyphus work --theme latte
```

---

## Work Plans (v3.0 YAML)

Sisyphus v3.0 uses structured YAML files instead of Markdown. This enables:
- **Dependency management**: Define which plans must complete before others
- **Automated validation**: Lint checks for cycles, missing references, invalid structure
- **Graph visualization**: See your project's dependency tree
- **Programmatic access**: Query and update tasks via CLI

### Basic Structure

```yaml
version: "3.0"

metadata:
  created_at: "2025-11-02T00:00:00Z"

work_plans:
  - id: plan-main
    name: "My Project"
    depends_on: []  # Optional: list plan IDs this depends on

    todos:
      - id: "1"
        title: "Database schema design"
        description: "Create PostgreSQL tables and indexes"
        status: pending

        children:  # Optional nested subtasks
          - id: "1.1"
            title: "Users table"
            status: pending

        references:  # Context and documentation
          - inline: "Use UUID for primary keys"

        verification_spec:  # Automated checks
          - type: bash
            description: "Check migration files"
            command: "ls migrations/*.sql"

      - id: "2"
        title: "API endpoint implementation"
        status: pending

    references:  # Plan-level references
      - ref_id: "postgres_docs"
        uri: "https://postgresql.org/docs/"
```

### Important Rules

1. **Status values**: `pending`, `in_progress`, `completed`, `blocked`
2. **Dependencies are validated**: Circular dependencies trigger lint errors
3. **References support inline or URI**: Use `inline` for quick notes, `uri` for external docs
4. **Children are limited to 1 level**: No deeply nested hierarchies

### Examples

See the `examples/` directory for complete examples:
- **`simple-project.yaml`**: Basic single-plan project
- **`multi-plan-dependencies.yaml`**: Multi-plan with dependency graph

```bash
# Browse examples
cat examples/simple-project.yaml

# Try the examples
sisyphus-speckit plan lint examples/simple-project.yaml
sisyphus-speckit plan graph examples/multi-plan-dependencies.yaml --format ascii
```

### Migration from v2.1 (ai-todolist.md)

If you have an old Markdown-based plan, use the converter:

```bash
sisyphus-speckit plan convert-legacy ai-todolist.md --output .sisyphus/tasks/main.yaml
```

See `docs/migration-v2-to-v3.md` for detailed migration guide.

### Cross-File Dependencies

Sisyphus v3.0 supports cross-file dependencies, allowing you to split large projects into multiple YAML files while maintaining execution order.

#### File Path Reference

Reference plans in other files using `file:` prefix:

```yaml
work_plans:
  - id: frontend-app
    name: "Frontend Application"
    depends_on:
      - file:backend.yaml#backend-api  # Relative or absolute path
```

The format is `file:<path>#<plan-id>`:
- **Path**: Relative (to current file) or absolute
- **Hash separator** (`#`): Separates file path from plan ID
- **Validation**: PlanLinter automatically checks file existence and plan ID validity

**Example:**
```yaml
# frontend.yaml
work_plans:
  - id: frontend-app
    depends_on:
      - file:../backend/api.yaml#backend-api
      - file:/absolute/path/auth.yaml#auth-service
```

#### Global Registry

For larger projects, use `.sisyphus/registry.yaml` to centrally manage all plan files:

```yaml
# .sisyphus/registry.yaml
version: "1.0"
plans:
  - file: tasks/backend.yaml
    plans:
      - backend-api
      - backend-auth
  - file: tasks/frontend.yaml
    plans:
      - frontend-app
```

Then reference plans using `registry:` prefix:

```yaml
# frontend.yaml
work_plans:
  - id: frontend-app
    depends_on:
      - registry:backend-api  # Resolved via registry
```

**Benefits:**
- Centralized plan management for large projects
- No need to track file paths in dependencies
- Easier refactoring (update registry instead of all YAML files)

#### When to Use Each Method

**File Path Reference** (`file:`):
- Small to medium projects (2-5 plan files)
- Direct 1-to-1 dependencies
- Explicit file relationships

**Registry Reference** (`registry:`):
- Large projects (10+ plan files)
- Complex dependency graphs
- Multiple plans depending on same external plan
- Team projects requiring centralized plan tracking

#### Validation

Run `sisyphus-speckit plan lint` to validate cross-file dependencies:

```bash
# Lint all plans in directory (auto-detects external references)
sisyphus-speckit plan lint .sisyphus/tasks/

# Lint specific file
sisyphus-speckit plan lint .sisyphus/tasks/frontend.yaml
```

PlanLinter automatically:
- Resolves `file:` references and checks if files exist
- Validates plan IDs exist in referenced files
- Loads and validates `registry.yaml` structure
- Detects circular dependencies across files

#### Visualization

Visualize cross-file dependency graphs:

```bash
# ASCII format (terminal-friendly)
sisyphus-speckit plan graph .sisyphus/tasks/ --format ascii

# Example output:
# backend-api (backend.yaml)
#   └─> frontend-app (frontend.yaml)

# Mermaid format
sisyphus-speckit plan graph .sisyphus/tasks/ --format mermaid

# PNG format (requires graphviz)
sisyphus-speckit plan graph .sisyphus/tasks/ --format png --output graph.png
```

#### Complete Example

See `examples/multi-file/` for a working example:

```bash
# View the example
cd examples/multi-file/

# Validate plans
sisyphus-speckit plan lint .

# Visualize dependencies
sisyphus-speckit plan graph . --format ascii

# Expected output:
# backend-api
#   └─> frontend-app
```

The example demonstrates:
- Backend plan with no dependencies (`backend.yaml`)
- Frontend plan depending on backend via file reference (`frontend.yaml`)
- Global registry setup (`.sisyphus/registry.yaml`)
- Both reference methods (file path and registry)

---

## Session Management

### What is a Session

Sisyphus remembers even if you stop mid-work. It saves to session files.

- **Location**: `./sessions/sessions.json`
- **Content**: Agent conversation history, work progress

### Resume Policy

- **Execute Phase**: Continues previous session. Maintains context.
- **Verify Phase**: Always new session. Unbiased verification.

### Session Reset

Once work is completely done, delete session-related content to avoid affecting the next task.

```sh
sisyphus reset
```

---

## Troubleshooting

### "OpenCode binary not found"

OpenCode not in PATH.

```sh
# Specify binary path directly
sisyphus work --agent opencode \
  --binary /path/to/opencode

# Or add to PATH
export PATH=$PATH:/path/to/opencode/bin
```

### "Port 8080 already in use"

OpenCode server already running or port used by another process.

```sh
# Use external server
sisyphus work --agent opencode \
  --opencode-server-url http://localhost:8080

# Check port
lsof -i :8080
```

### "Session file corrupted"

Session file recovery failed. Delete and restart.

```sh
rm ./sessions/sessions.json
```

---

## Advanced Features

### Multi-Plan Projects

For large projects, split work into multiple interdependent plans:

```bash
# Create foundation plan
sisyphus-speckit plan init --destination .sisyphus/tasks/foundation.yaml

# Create main plan (depends on foundation)
sisyphus-speckit plan init --destination .sisyphus/tasks/main.yaml

# Edit main.yaml to add dependency:
# depends_on: ["plan-foundation"]

# Visualize the full graph
sisyphus-speckit plan graph .sisyphus/tasks/ --format ascii
```

Output:
```
plan-foundation
  └─> plan-main
```

Sisyphus will automatically:
1. Execute plan-foundation first
2. Wait until all tasks complete
3. Move to plan-main automatically

### Working with Multiple Worktrees

Sisyphus v3.0 supports Git worktrees for parallel development:

```bash
# Create worktree for feature branch
git worktree add ../sisyphus-feature feature/auth

# Each worktree has independent status
cd ../sisyphus-feature
sisyphus-speckit task continue  # Works on feature/auth tasks

cd ../sisyphus
sisyphus-speckit task continue  # Works on main branch tasks
```

The `.sisyphus/status.json` file tracks the current plan per worktree.

### Custom Working Directory

Use `--cwd` to run Sisyphus from a different directory:

```bash
# Manage tasks in a subdirectory
sisyphus-speckit plan lint --cwd ./temp/

# Execute tasks in experimental directory
sisyphus-speckit task continue --cwd ./experiments/ --execute claude:sonnet
```

---

### Running Tests

Sisyphus uses pytest. Thanks to anyio, both asyncio and trio backends are tested.

```sh
# All tests (461 tests × 2 = 922 executions)
uv run pytest

# Verbose output
uv run pytest -v

# Stop at first failure
uv run pytest -x

# Specific file only
uv run pytest sisyphus/agents/tests/test_claude.py

# Check coverage
uv run pytest --cov=sisyphus --cov-report=html
```

### Code Quality Checks

```sh
# Type checking
uv run basedpyright

# Lint
uv run ruff check

# Auto-fix lint issues
uv run ruff check --fix

# Format
uv run ruff format

# All at once
uv run basedpyright && uv run ruff check && uv run pytest
```

### Project Structure

```
sisyphus/
├── sisyphus/              # Main package
│   ├── agents/           # Agent implementations
│   │   ├── base.py       # Agent Protocol
│   │   ├── claude.py     # Claude agent
│   │   └── opencode.py   # OpenCode agent
│   ├── core/             # Core logic
│   │   ├── loop.py       # ExecutionLoop (execute-verify orchestration)
│   │   ├── prompts.py    # Prompt interpretation
│   │   ├── session.py    # Session save/restore
│   │   └── tasks.py      # Task validation (ai-todolist.md)
│   ├── ui/               # User interface
│   │   ├── tui/          # Textual TUI
│   │   └── cli/          # Rich CLI
│   ├── utils/            # Utilities
│   └── cli.py            # Typer CLI entry point
├── prompts/              # Default prompts
│   ├── execute_command.md
│   └── architect_command.md
├── sessions/             # Session storage (auto-generated)
├── logs/                 # Log files (auto-generated)
└── pyproject.toml        # Project configuration
```

### Coding Rules

Sisyphus is strict. Even with itself.

- **Type hints required** - All function parameters and return values must have types (ruff ANN001)
- **Double quotes** - Wrap strings with `"`
- **Use anyio** - asyncio and trio compatibility
- **Given-When-Then** - Test structure
- **Protocol-based** - typing.Protocol instead of ABC (PEP 544)

---

## Tech Stack

Sisyphus stands on modern Python ecosystem.

### Core

- **Python 3.12** - Latest type hinting and performance
- **anyio** - asyncio and trio abstraction, one codebase for two backends
- **Typer** - CLI framework
- **Textual** - Terminal UI
- **Rich** - Beautiful console output

### Agent Communication

- **claude-agent-sdk** - Claude official SDK
- **httpx** - OpenCode REST API communication
- **aiofiles** - Async file I/O

### Development Tools

- **basedpyright** - Type checker (standard mode)
- **ruff** - Linter and formatter in one
- **pytest + pytest-anyio** - Test framework
- **uv** - Fast package manager

### Design

- **Protocol-based** - Interface separation (PEP 544)
- **Dependency Injection** - Loose coupling
- **Factory Pattern** - Agent/UI creation
- **SOLID** - Object-oriented 5 principles

---

## License

Sisyphus is distributed under **Sustainable Use License 1.0**.

### In Simple Terms

✅ **What you CAN do:**
- Personal use and learning
- Internal business use at your company
- Modify and improve code
- Distribute for free (non-commercial purposes)

❌ **What you CANNOT do:**
- Commercial sale
- Provide as SaaS
- Redistribute as paid service

### Details

For full license terms, see [LICENSE.md](LICENSE.md).

### Enterprise License

Need commercial use or SaaS provision? Contact us separately.

## For Developers

### Release Process

Sisyphus uses automated GitHub Actions for releases.

1. Go to Actions tab in GitHub repository
2. Select "Bump Version and Release" workflow
3. Click "Run workflow"
4. Choose version type:
   - **patch**: Bug fixes (0.1.0 → 0.1.1)
   - **minor**: New features (0.1.0 → 0.2.0)
   - **major**: Breaking changes (0.1.0 → 1.0.0)
5. Click "Run workflow" button

The workflow will:
- Update version in pyproject.toml
- Create git commit and tag
- Create GitHub Release
- Automatically publish to PyPI

### Manual Publishing (if needed)

```sh
# Build package
uv build

# Publish to PyPI
uv publish

# Publish to TestPyPI (for testing)
uv publish --publish-url https://test.pypi.org/legacy/
```

## Contributing

[Contribution guidelines needed]

## Support

[Support information needed]
