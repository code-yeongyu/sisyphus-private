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

Sisyphus requires Python 3.12 or higher. We recommend using the uv package manager.

```sh
# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the project
git clone <repository-url>
cd sisyphus

# Install dependencies
uv sync
```

Run directly in development mode:
```sh
uv run sisyphus work
```

### First Task

1. **Create Work Plan** - Make an `ai-todolist.md` file.
   - Write what to build.
   - Write how to build it.
   - List tasks with checkboxes (`- [ ]`).
   - *This is how it works now, but automatic work plan generation will be released soon.*

2. **Run Sisyphus**
   ```sh
   uv run sisyphus work
   ```

3. **Observe** - TUI appears showing the agents working.
   - Check progress in chat log
   - View current stage in status panel
   - Send messages if needed

4. **Complete** - Sisyphus notifies when all tasks are done.

---

## Commands

### `sisyphus work`

Starts the work. Uses Claude agent and TUI mode by default.

```sh
# Basic execution (Claude + TUI)
uv run sisyphus work

# CLI mode (useful for automation)
uv run sisyphus work --no-tui

# Use OpenCode agent
uv run sisyphus work --agent opencode
```

### Agent Selection

Sisyphus supports two agents.

**Claude**
```sh
# Default model
uv run sisyphus work --agent claude

# Specify model
uv run sisyphus work --agent claude:sonnet

# Adjust SDK options
uv run sisyphus work --agent claude \
  --execute-sdk-options '{"temperature": 0.8}'
```

**OpenCode** (Alpha Support)
```sh
# Auto-start server
uv run sisyphus work --agent opencode

# Use external server
uv run sisyphus work --agent opencode \
  --opencode-server-url http://localhost:8080
```

### Separate Execute and Verify

This is Sisyphus's core feature. You can use different agents for execution and verification.

```sh
# Execute with Claude, verify with OpenCode
uv run sisyphus work \
  --execute claude:sonnet \
  --verify opencode

# Execute only, skip verification
uv run sisyphus work --execute claude
```

The verification agent always starts with a fresh session. Clean context. No bias.

### Prompt Customization

You can change the instructions given to agents.

```sh
# Slash commands (built-in prompts)
uv run sisyphus work \
  --execute-prompt /execute \
  --verify-prompt /architect

# Read from files
uv run sisyphus work \
  --execute-prompt prompts/my-execute.md \
  --verify-prompt prompts/my-verify.md

# Pass as direct text
uv run sisyphus work \
  --execute-prompt "Complete all tasks in ai-todolist.md"

# Append additional instructions
uv run sisyphus work \
  --execute-extra-prompt "Must use type hints" \
  --verify-extra-prompt "Focus on security vulnerabilities"
```

### `sisyphus reset`

Clean up the work environment.

```sh
# Delete only sessions and logs
uv run sisyphus reset

# Delete work plans too (start from scratch)
uv run sisyphus reset --include-task-specs
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
uv run sisyphus work --theme system

# Dark mode (Catppuccin Mocha)
uv run sisyphus work --theme mocha

# Light mode (Catppuccin Latte)
uv run sisyphus work --theme latte
```

---

## Work Plan (`ai-todolist.md`)

This is Sisyphus's boulder. Fortunately, Sisyphus can push the boulder to the mountain top. Just keep pushing.

### Basic Structure

  ```markdown
  # User Request

  Write what to build here.

  ## Task List

  - [ ] Task 1: Database schema design
  - [ ] Task 2: API endpoint implementation
  - [ ] Task 3: Test code writing

  ## Completion Flag

  is_all_goals_accomplished = FALSE
  ```

### Important Rules

1. **Checkboxes are sacred** - `- [ ]` is incomplete, `- [x]` is complete
2. **Completion flag doesn't lie** - Only changes to `TRUE` when all tasks are done
3. **Sisyphus reads this document repeatedly** - Write clearly

When work is complete:
- All checkboxes become `- [x]`
- `is_all_goals_accomplished = TRUE`

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
uv run sisyphus reset
```

---

## Troubleshooting

### "OpenCode binary not found"

OpenCode not in PATH.

```sh
# Specify binary path directly
uv run sisyphus work --agent opencode \
  --binary /path/to/opencode

# Or add to PATH
export PATH=$PATH:/path/to/opencode/bin
```

### "Port 8080 already in use"

OpenCode server already running or port used by another process.

```sh
# Use external server
uv run sisyphus work --agent opencode \
  --opencode-server-url http://localhost:8080

# Check port
lsof -i :8080
```

### "Session file corrupted"

Session file recovery failed. Delete and restart.

```sh
rm ./sessions/sessions.json
```

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

## Contributing

[Contribution guidelines needed]

## Support

[Support information needed]
