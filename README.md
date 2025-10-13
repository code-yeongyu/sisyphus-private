# Sisyphus

**A multi-agent orchestration system supporting Claude and OpenCode agents with flexible execution strategies and interactive TUI/CLI interfaces.**

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [CLI Options Reference](#cli-options-reference)
- [Agent-Specific Features](#agent-specific-features)
- [Prompt Customization](#prompt-customization)
- [Session Management](#session-management)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Tech Stack](#tech-stack)

---

## Overview

Sisyphus is a Python 3.12-based multi-agent orchestration system that allows you to:

- **Run multiple AI agents**: Claude (Anthropic), OpenCode (REST API-based)
- **Separate execution phases**: Use different agents for execute and verify phases
- **Choose your interface**: Interactive TUI (Textual) or CLI (Rich) mode
- **Manage sessions**: Persistent session storage with resume capability
- **Customize prompts**: Slash commands, file paths, plain text, or direct input

Built with SOLID principles, Protocol-based interfaces, and anyio for asyncio/trio compatibility.

---

## Key Features

### 🤖 Multi-Agent Support
- **Claude Agent**: Official SDK integration with session resume support
- **OpenCode Agent**: REST API with SSE streaming and auto-server startup

### 🔄 Two-Phase Execution
- **Execute Phase**: Main task execution
- **Verify Phase**: Independent verification with a new session
- Use the same agent for both phases or mix different agents

### 🖥️ Dual UI Modes
- **TUI Mode** (default): OpenCode-style interactive terminal UI
  - Split layout: chat log (top 70%), status panel (middle 20%), input bar (bottom 10%)
  - Interactive message queuing (Claude & OpenCode only)
  - Keyboard shortcuts: `Ctrl+C` (interrupt), `Ctrl+D` (exit), `UP` (edit message)
- **CLI Mode** (`--no-tui`): Rich-based console output
  - Color-coded messages by phase (execute: yellow, verify: cyan)
  - Suitable for non-interactive environments

### 💾 Session Management
- Persistent session storage in `./sessions/`
- Automatic session resume (Claude)
- File locking for concurrent access safety
- Atomic writes with corruption recovery

### 📝 Flexible Prompt System
- **Slash commands**: `/execute`, `/architect` (built-in prompts)
- **File paths**: `prompts/custom.md` (read from file)
- **Plain text**: `plain-text` (embedded default prompts)
- **Direct input**: Any string not matching above patterns
- **Extra prompts**: Append additional instructions with `--execute-extra-prompt` / `--verify-extra-prompt`

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                           │
│                        (sisyphus/cli.py)                          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      UI Layer (Protocol)                          │
│  ┌──────────────────┐              ┌──────────────────┐          │
│  │   TUI (Textual)  │              │   CLI (Rich)     │          │
│  │  - ChatLog       │              │  - Console       │          │
│  │  - StatusPanel   │              │  - Markdown      │          │
│  │  - InputBar      │              │                  │          │
│  └──────────────────┘              └──────────────────┘          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      ExecutionLoop (Core)                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │ PromptResolver │  │  SessionStore  │  │ TaskValidator  │     │
│  │  - Slash cmd   │  │  - File lock   │  │  - ai-todolist │     │
│  │  - Plain text  │  │  - Atomic save │  │    validation  │     │
│  │  - File path   │  │                │  │                │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Phase 1: Execute  →  Phase 2: Verify (new session)    │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Agent Layer (Protocol)                        │
│  ┌─────────────┐                    ┌─────────────────┐          │
│  │ ClaudeAgent │                    │ OpenCodeAgent   │          │
│  │  - SDK      │                    │  - anyio        │          │
│  │  - Resume   │                    │    subprocess  │          │
│  │  - Interactive│                  │  - REST API     │          │
│  │             │                    │  - SSE stream   │          │
│  │             │                    │  - Interactive  │          │
│  └─────────────┘                    └─────────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. CLI parses options → creates agents via factory
2. UI renders messages from ExecutionLoop
3. ExecutionLoop orchestrates Execute → Verify phases
4. Agents communicate via Protocol methods
5. SessionStore persists state with file locks
6. Utils provide cross-cutting concerns (process, logging)

---

## Installation

### Using uv (Recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd sisyphus

# Sync dependencies
uv sync
```

### Using pip (Alternative)

If you don't have `uv`, you can use pip with a virtual environment:

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

**Note**: The project requires Python 3.12 or higher.

---

## Quick Start

### Basic Usage (Claude + TUI)

```bash
# Run with default settings (Claude agent, TUI mode, default prompts)
uv run sisyphus run
```

This will:
- Use Claude agent for both execute and verify phases
- Launch interactive TUI
- Load default prompts from `prompts/execute_command.md` and `prompts/architect_command.md`
- Create/resume sessions in `./sessions/`

### CLI Mode (No TUI)

```bash
# Use CLI mode for non-interactive environments
uv run sisyphus run --no-tui
```

### Help

```bash
# See all available options
uv run sisyphus run --help
```

---

## Usage Examples

### 1. Basic Execution with Different Agents

```bash
# Use Claude (default)
uv run sisyphus run --agent claude

# Use OpenCode
uv run sisyphus run --agent opencode
```

### 2. Specify Agent Model

```bash
# Claude with specific model
uv run sisyphus run --agent claude:sonnet

# OpenCode (model selection not applicable)
uv run sisyphus run --agent opencode
```

### 3. Separate Execute and Verify Agents

```bash
# Execute with Claude Sonnet, verify with OpenCode
uv run sisyphus run --execute claude:sonnet --verify opencode

# Execute with OpenCode, verify with Claude
uv run sisyphus run --execute opencode --verify claude

# Execute only (no verify phase)
uv run sisyphus run --execute claude
```

### 4. Custom Prompts

```bash
# Use custom prompt files
uv run sisyphus run \
  --execute-prompt my-prompts/custom-execute.md \
  --verify-prompt my-prompts/custom-verify.md

# Use slash commands (built-in prompts)
uv run sisyphus run \
  --execute-prompt /execute \
  --verify-prompt /architect

# Use plain text (embedded default prompts)
uv run sisyphus run \
  --execute-prompt plain-text \
  --verify-prompt plain-text

# Direct text input
uv run sisyphus run \
  --execute-prompt "Complete the task in ai-todolist.md"
```

### 5. Extra Prompts (Append Instructions)

```bash
# Add extra instructions to execute phase
uv run sisyphus run \
  --execute-extra-prompt "Focus on performance optimization"

# Add extra instructions to both phases
uv run sisyphus run \
  --execute-extra-prompt "Use modern Python 3.12 features" \
  --verify-extra-prompt "Check for type safety violations"
```

### 6. SDK Options (JSON)

```bash
# Pass SDK options to Claude agent
uv run sisyphus run --agent claude \
  --execute-sdk-options '{"temperature": 0.7, "max_tokens": 4096}'

# Different options for execute and verify phases
uv run sisyphus run \
  --execute claude \
  --verify claude \
  --execute-sdk-options '{"temperature": 0.9}' \
  --verify-sdk-options '{"temperature": 0.3}'
```

### 7. OpenCode Server URL

```bash
# Use external OpenCode server instead of auto-starting
uv run sisyphus run --agent opencode \
  --opencode-server-url http://localhost:8080
```

### 8. CLI Mode for Automation

```bash
# Non-interactive CLI mode (suitable for CI/CD)
uv run sisyphus run --agent claude --no-tui

# Redirect output to file
uv run sisyphus run --agent opencode --no-tui > output.log 2>&1
```

### 9. Complex Workflow

```bash
# Execute with Claude Sonnet, verify with OpenCode
# Custom prompts, extra instructions, CLI mode
uv run sisyphus run \
  --execute claude:sonnet \
  --verify opencode \
  --execute-prompt prompts/custom-execute.md \
  --verify-prompt prompts/custom-verify.md \
  --execute-extra-prompt "Prioritize code quality" \
  --verify-extra-prompt "Focus on security and edge cases" \
  --execute-sdk-options '{"temperature": 0.8}' \
  --no-tui
```

---

## CLI Options Reference

### Agent Selection

| Option | Type | Description |
|--------|------|-------------|
| `--agent`, `-a` | `str` | Agent type for both execute and verify phases. Options: `claude`, `opencode`. Format: `AGENT[:MODEL]` (e.g., `claude:sonnet`). **Cannot be used with `--execute` or `--verify`.** |
| `--execute` | `str` | Execute phase agent. Format: `AGENT[:MODEL]`. **Overrides `--agent` for execute phase.** |
| `--verify` | `str` | Verify phase agent. Format: `AGENT[:MODEL]`. **Overrides `--agent` for verify phase.** If omitted, no verify phase. |

**Default**: If neither `--agent` nor `--execute` is specified, defaults to `claude`.

### Prompt Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--execute-prompt` | `str` | `prompts/execute_command.md` | Execute prompt. Options: file path, slash command (`/execute`), `plain-text`, or direct text. |
| `--verify-prompt` | `str` | `prompts/architect_command.md` | Verify prompt. Options: file path, slash command (`/architect`), `plain-text`, or direct text. |
| `--execute-extra-prompt` | `str` | `None` | Extra instructions appended to execute prompt. |
| `--verify-extra-prompt` | `str` | `None` | Extra instructions appended to verify prompt. |

### Binary Configuration

| Option | Type | Description |
|--------|------|-------------|
| `--binary` | `Path` | Common binary path for all agents. Auto-detected if not specified. |
| `--execute-binary` | `Path` | Execute phase binary. **Overrides `--binary` for execute.** |
| `--verify-binary` | `Path` | Verify phase binary. **Overrides `--binary` for verify.** |

**Priority**: Specific binary (`--execute-binary` / `--verify-binary`) > Common binary (`--binary`) > Auto-detection.

### SDK Options

| Option | Type | Description |
|--------|------|-------------|
| `--execute-sdk-options` | `str` (JSON) | SDK options for execute agent (e.g., `{"temperature": 0.7}`). Merged with model from agent spec. |
| `--verify-sdk-options` | `str` (JSON) | SDK options for verify agent (e.g., `{"max_tokens": 4096}`). Merged with model from agent spec. |

**Format**: Must be valid JSON. Invalid JSON will raise an error.

### Server Configuration

| Option | Type | Description |
|--------|------|-------------|
| `--opencode-server-url` | `str` | External OpenCode server URL (e.g., `http://localhost:8080`). If not specified, auto-starts local server. Must be valid HTTP/HTTPS URL. |

### UI Mode

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--no-tui` | `bool` | `False` | Disable TUI, use CLI mode. Suitable for non-interactive environments or CI/CD. |

### Logging

| Option | Type | Description |
|--------|------|-------------|
| `--log` | `Path` | Log file path. If not specified, logs are written to `./logs/` directory with auto-generated names. |

---

## Agent-Specific Features

### Claude Agent

**Features:**
- Official `claude-agent-sdk` integration
- Session resume support (preserves conversation history)
- Interactive message input (TUI mode only)
- Flexible SDK options via JSON

**Model Selection:**
- Specify model with `:` separator (e.g., `claude:sonnet`)
- Default: SDK default model

**Session Management:**
- Sessions stored in `./sessions/sessions.json`
- Resume automatically on next run

**Example:**
```bash
uv run sisyphus run --agent claude:sonnet \
  --execute-sdk-options '{"temperature": 0.8, "max_tokens": 8192}'
```

### OpenCode Agent

**Features:**
- REST API with SSE streaming
- Auto-server startup (`opencode serve`)
- Health check with retries (max 5 attempts, 2s interval)
- Interactive message input (TUI mode only)

**Server Management:**
- Auto-start: Default behavior
- External server: Use `--opencode-server-url`

**Session Management:**
- Server-managed sessions (format: `ses_xxx`)
- Sessions stored in `./sessions/sessions.json`

**Timeouts:**
- Server startup: 10s
- Health check: 2s per attempt
- SSE idle: 60s

**Example:**
```bash
# Auto-start server
uv run sisyphus run --agent opencode

# Use external server
uv run sisyphus run --agent opencode \
  --opencode-server-url http://localhost:8080
```

---

## Prompt Customization

Sisyphus supports multiple prompt formats:

### 1. Slash Commands (Built-in)

```bash
# Use built-in execute prompt
uv run sisyphus run --execute-prompt /execute

# Use built-in architect (verify) prompt
uv run sisyphus run --verify-prompt /architect
```

**Available Commands:**
- `/execute`: Default execute prompt
- `/architect`: Default verify prompt

### 2. File Paths

```bash
# Load prompt from file
uv run sisyphus run --execute-prompt prompts/custom.md

# Absolute path
uv run sisyphus run --execute-prompt /home/user/prompts/my-prompt.txt
```

### 3. Plain Text (Embedded Defaults)

```bash
# Use embedded default prompts
uv run sisyphus run --execute-prompt plain-text --verify-prompt plain-text
```

### 4. Direct Text Input

```bash
# Pass prompt directly as string
uv run sisyphus run --execute-prompt "Complete all tasks in ai-todolist.md"
```

### 5. Extra Prompts (Append)

```bash
# Append extra instructions to base prompt
uv run sisyphus run \
  --execute-prompt /execute \
  --execute-extra-prompt "Use type hints for all functions"
```

**Format**: Extra prompts are appended with `\n\n` separator.

---

## Session Management

### Storage Location

Sessions are stored in `./sessions/sessions.json` with the following structure:

```json
{
  "claude": {
    "session_id": "uuid-v4",
    "agent_type": "claude",
    "created_at": "2025-10-09T12:00:00Z",
    "last_used": "2025-10-09T13:30:00Z"
  },
  "opencode": {
    "session_id": "ses_xxx",
    "agent_type": "opencode",
    "created_at": "2025-10-09T12:00:00Z",
    "last_used": "2025-10-09T13:30:00Z"
  }
}
```

### Session Resume

- **Execute Phase**: Resumes previous session if available
- **Verify Phase**: **Always creates a new session** (independent verification)

### Session Lifecycle

1. **First Run**: New session created, ID generated
2. **Subsequent Runs**: Existing session resumed (execute phase only)
3. **Verify Phase**: New session for each verification

### Manual Session Management

```bash
# View sessions
cat ./sessions/sessions.json

# Clear all sessions (start fresh)
rm ./sessions/sessions.json

# Clear specific agent session
# Edit ./sessions/sessions.json and remove the agent entry
```

---

## Troubleshooting

### Common Issues

#### 1. `Agent binary not found`

**Problem**: OpenCode binary not in PATH.

**Solution**:
```bash
# Specify binary path explicitly
uv run sisyphus run --agent opencode --binary /path/to/opencode

# Or add to PATH
export PATH=$PATH:/path/to/agent/bin
```

#### 2. `Invalid JSON in SDK options`

**Problem**: Malformed JSON in `--execute-sdk-options` or `--verify-sdk-options`.

**Solution**:
```bash
# Use single quotes around JSON, double quotes inside
uv run sisyphus run --agent claude \
  --execute-sdk-options '{"temperature": 0.7}'

# Validate JSON before use
echo '{"temperature": 0.7}' | jq .
```

#### 3. `OpenCode server failed to start`

**Problem**: Server startup timeout or port conflict.

**Solution**:
```bash
# Use external server
opencode serve &  # Start manually
uv run sisyphus run --agent opencode \
  --opencode-server-url http://localhost:8080

# Or check if port 8080 is free
lsof -i :8080
```

#### 4. `Cannot use --agent with --execute or --verify`

**Problem**: Conflicting agent options.

**Solution**:
```bash
# Use either --agent (same for both phases)
uv run sisyphus run --agent claude

# Or --execute / --verify (different per phase)
uv run sisyphus run --execute claude --verify opencode

# But NOT both
```

#### 5. TUI rendering issues

**Problem**: Flickering or layout issues in TUI.

**Solution**:
```bash
# Use CLI mode instead
uv run sisyphus run --no-tui

# Or update terminal emulator
# Ensure TERM variable is set correctly
echo $TERM  # Should be xterm-256color or similar
```

#### 6. Session corruption

**Problem**: `sessions.json` file corrupted.

**Solution**:
```bash
# SessionStore has automatic backup recovery
# If recovery fails, manually delete and restart
rm ./sessions/sessions.json
uv run sisyphus run  # Will create new sessions
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd sisyphus

# Install dependencies
uv sync

# Verify installation
uv run sisyphus --help
```

### Running Tests

```bash
# Run all tests (both asyncio and trio backends)
uv run pytest

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Run specific test file
uv run pytest sisyphus/agents/tests/test_claude.py

# Run with coverage
uv run pytest --cov=sisyphus --cov-report=html
```

**Test Count**: 461 tests (asyncio + trio backends auto-tested by pytest-anyio)

### Code Quality Checks

```bash
# Type checking
uv run basedpyright

# Linting
uv run ruff check

# Auto-fix linting issues
uv run ruff check --fix

# Formatting
uv run ruff format

# Run all checks
uv run basedpyright && uv run ruff check && uv run pytest
```

### Project Structure

```
sisyphus/
├── prompts/               # Default prompt files
│   ├── execute_command.md
│   └── architect_command.md
├── sisyphus/
│   ├── agents/           # Agent implementations
│   │   ├── base.py       # Agent Protocol
│   │   ├── claude.py     # ClaudeAgent
│   │   └── opencode.py   # OpenCodeAgent
│   ├── core/             # Core business logic
│   │   ├── loop.py       # ExecutionLoop
│   │   ├── prompts.py    # PromptResolver
│   │   ├── session.py    # SessionStore
│   │   └── tasks.py      # TaskValidator
│   ├── ui/               # UI implementations
│   │   ├── base.py       # UIProtocol
│   │   ├── tui/          # Textual TUI
│   │   └── cli/          # Rich CLI
│   ├── utils/            # Utilities
│   │   ├── errors.py     # Custom exceptions
│   │   ├── logging.py    # LoggerFactory
│   │   ├── process.py    # ProcessManager
│   │   └── types.py      # Common types
│   ├── cli.py            # Typer CLI
│   └── __main__.py       # Entry point
├── logs/                 # Log files (auto-generated)
├── sessions/             # Session storage (auto-generated)
└── pyproject.toml        # Project configuration
```

### Code Style

- **Type Hints**: Required for all function parameters and return values (ANN001)
- **Quotes**: Double quotes for all strings
- **Async**: anyio for asyncio/trio compatibility
- **Tests**: Given-When-Then pattern, `pytest.mark.anyio` for async support

---

## Tech Stack

### Core Dependencies
- **Python**: 3.12.x
- **Async Runtime**: anyio (asyncio + trio support)
- **CLI Framework**: Typer
- **TUI Framework**: Textual
- **CLI Rendering**: Rich
- **HTTP Client**: httpx (for OpenCode)
- **Claude SDK**: claude-agent-sdk
- **Testing**: pytest + pytest-anyio

### Development Tools
- **Type Checking**: basedpyright (standard mode)
- **Linting & Formatting**: ruff
- **Package Manager**: uv

### Design Patterns
- **Protocol-based interfaces** (PEP 544): Agent, UIProtocol
- **Dependency Injection**: ExecutionLoop depends on protocols, not concrete classes
- **Factory Pattern**: Agent and UI creation
- **Strategy Pattern**: Session resume strategies
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion

---

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]
