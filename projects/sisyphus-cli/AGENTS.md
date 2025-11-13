# PROJECT KNOWLEDGE BASE

**Generated:** 2025-11-03 22:27:16 KST
**Commit:** 60cc0c4
**Branch:** master
**Repo:** https://github.com/code-yeongyu/sisyphus.git

## TECH STACK

**Language:** Python 3.12+
**CLI:** Typer 0.15+ → command routing, argument parsing
**TUI:** Textual 1.0+ → interactive terminal UI (asyncio only)
**Output:** Rich 13+ → formatted console output
**Async:** anyio 4.11+ → asyncio/trio compatibility layer
**Agent SDK:** claude-agent-sdk 0.1+ → Claude official SDK
**HTTP:** httpx 0.28+ → OpenCode REST API, async requests
**File I/O:** aiofiles 24+ → async file operations
**Config:** pydantic 2.0+ → type-safe config models
**YAML:** ruamel.yaml 0.18+ → v3.0 WorkPlan format

**Key Dependencies:**
- trio 0.31+: Alternative async backend → anyio enables single codebase for both asyncio+trio
- uvloop 0.21+: High-performance event loop → asyncio accelerator
- catppuccin 2.5+: Theme system → Mocha (dark) + Latte (light) themes

**Why anyio?** Single codebase runs both asyncio (TUI) + trio (CLI) → extensive test coverage (tests × 2 backends automatically)

## ARCHITECTURE

```mermaid
graph TB
    CLI[cli.py<br/>Typer] --> CMD{Command Router}

    CMD -->|sisyphus work| WORK[work.py<br/>Work command]
    CMD -->|sisyphus task| TASK[task.py<br/>Task navigation]
    CMD -->|sisyphus plan| PLAN[plan.py<br/>Plan management]

    TASK --> TM[TaskManager<br/>DFS navigation]
    TASK --> STATUS[StatusManager<br/>Current plan]

    PLAN --> LOADER[plans/loader.py<br/>load_plan]
    PLAN --> LINTER[PlanLinter<br/>Validation]
    PLAN --> GRAPH[GraphRenderer<br/>Mermaid/ASCII/PNG]

    TM --> MODELS[WorkPlan Models<br/>Pydantic]
    LOADER --> MODELS
    STATUS --> MODELS
```

**Pattern:** Protocol-based (PEP 544) → Agent, UIProtocol decoupled
**Entry:** sisyphus/cli.py → Typer app, command registration
**Flow:** CLI → Command Router → Task/Work/Plan handlers → Agents/UI

**Core Components:**
- **TaskManager**: DFS-based task navigation (current/next/previous), completion checks
- **StatusManager**: Tracks current plan per git worktree (.sisyphus/status.json)
- **load_plan()**: Parses v3.0 YAML → Pydantic models (WorkPlan, Todo, Reference)
- **PlanLinter**: Validates circular deps, missing references, malformed YAML
- **GraphRenderer**: Visualizes plan dependencies (Mermaid/ASCII/PNG)

**Task Navigation Flow:**
1. CLI parses args → `task continue`, `task current`, `task next`
2. StatusManager resolves current plan from status.json
3. TaskManager loads YAML → finds current/next task using DFS algorithm
4. Task commands display/modify task status
5. Verification commands (`verify bash/llm/manual`) check completion criteria

**Deviations from Standard:**
- **v3.0 YAML plans**: Not Markdown, structured YAML with dependency graph support
- **Protocol over ABC**: Uses `typing.Protocol` (runtime_checkable), not Abstract Base Classes
- **anyio everywhere**: All async code uses anyio (`anyio.sleep`, `anyio.create_task_group`), not raw asyncio
- **Dual backend tests**: pytest-anyio auto-runs tests on both asyncio + trio
- **TUI forces asyncio**: Textual limitation, CLI auto-selects via anyio
- **Plan-centric**: No in-memory state, YAML files are source of truth

## DEPENDENCIES

**External Services:**
- Claude API: ClaudeAgent → Anthropic SDK, session management
- OpenCode server: OpenCodeAgent → REST @ localhost:8080 (auto-start or external)

**Key Integrations:**
- ClaudeAgent: SDK session resume, interactive `get_input()` via TUI
- OpenCodeAgent: SSE streaming, 60s idle timeout, subprocess health check

**Plan Storage:**
`.sisyphus/tasks/*.yaml` → WorkPlan v3.0 format
`.sisyphus/status.json` → Current plan tracking per worktree

## PROJECT STRUCTURE

```
sisyphus-cli/
├── sisyphus/               # Main package (not src/)
│   ├── cli/               # Command handlers
│   │   ├── plan.py        # Plan management (init/lint/graph/export)
│   │   ├── task.py        # Task execution (continue/current/next/verify)
│   │   ├── work.py        # Legacy work command + ignore/clean-history
│   │   └── reset.py       # Cleanup command
│   ├── agents/            # Agent implementations
│   │   ├── base.py        # Agent Protocol
│   │   ├── claude.py      # ClaudeAgent
│   │   └── opencode.py    # OpenCodeAgent
│   ├── core/              # Business logic
│   │   ├── plans/         # YAML models & loader (WorkPlan, Todo, loader.py)
│   │   ├── converters/    # v2.1 Markdown → v3.0 YAML converter
│   │   ├── exporters/     # YAML → Markdown exporter
│   │   ├── graph/         # Dependency graph renderer
│   │   ├── status/        # Status tracking (manager.py)
│   │   ├── task_manager.py # DFS task navigation
│   │   └── plan_linter.py # Validation (cycles, refs)
│   ├── ui/                # UI layer
│   │   ├── tui/           # Textual TUI (app.py + components/)
│   │   ├── cli/           # Rich CLI (console.py)
│   │   ├── base.py        # UIProtocol
│   │   └── themes.py      # Catppuccin themes
│   ├── utils/             # Cross-cutting
│   └── cli.py             # Typer entry point
├── docs/                  # Migration guides, architecture
├── examples/              # Sample YAML plans
└── tests/                 # Test suite
```

**Non-Standard:**
- `sisyphus/` package at root (not `src/sisyphus/`)
- `.sisyphus/` directory for plans/status (not `plans/` or `tasks/`)
- `cli/` subdirectory splits commands by domain (plan/task/work/reset)

## PRD

```mermaid
graph LR
    P[Problem:<br/>LLM agents skip work<br/>lack quality gates] --> S[Solution:<br/>YAML-based plans<br/>+dependency graph<br/>+verification]

    S --> F1[Structured plans<br/>YAML v3.0]
    S --> F2[Multi-agent support<br/>Claude/OpenCode]
    S --> F3[Dual UI<br/>TUI/CLI]
    S --> F4[Plan dependencies<br/>Graph validation]

    F1 --> B1[Clear work breakdown<br/>Automated lint]
    F2 --> B2[Flexible execution<br/>Mix agents]
    F3 --> B3[Dev-friendly UX<br/>Interactive+automation]
    F4 --> B4[Large projects<br/>Multi-plan orchestration]
```

**Core Purpose:** Multi-agent orchestration CLI that compiles natural language work plans (YAML) into production code via LLM agents

**Key Features:**
- **v3.0 YAML Plans**: Structured work plans with dependency graph, validation, visualization
- **Multi-Agent**: Claude (SDK), OpenCode (REST) → mix agents per task
- **Task Navigation**: Auto-find current/next task based on status, respect dependencies
- **Plan Management**: `init`, `lint`, `graph`, `export`, `convert-legacy`
- **Task Execution**: `continue`, `current`, `next`, `verify`
- **Dual UI**: TUI (interactive Textual), CLI (automation Rich output)
- **Git Integration**: `ignore` (add to .gitignore), `clean-history` (remove from git)
- **Theme Support**: Auto-detect system theme, manual Catppuccin Mocha/Latte

**Target Users:** Developers needing multi-agent workflows for large projects with clear task breakdown

**Unique Aspects:**
- YAML plans as source of truth (not in-memory or Markdown)
- Dependency graph between multiple plans → multi-plan projects
- Lint checks for circular deps, missing references
- Graph visualization (Mermaid/ASCII/PNG via graphviz)
- anyio abstraction → CLI supports both asyncio + trio, tests run 2× automatically
- Protocol-based design → easy agent addition (5 methods)
- DFS-based task navigation → respects hierarchical task structure

## DEVELOPMENT COMMANDS

**Test:**
```bash
# All tests (auto-runs on asyncio + trio)
uv run pytest

# Single file
uv run pytest sisyphus/agents/tests/test_claude.py

# Verbose + stop on first failure
uv run pytest -v -x

# Coverage
uv run pytest --cov=sisyphus --cov-report=html
```

**Type Check:**
```bash
uv run basedpyright
```

**Lint + Format:**
```bash
uv run ruff check        # Lint
uv run ruff check --fix  # Auto-fix
uv run ruff format       # Format
```

**Run (various modes):**
```bash
# v3.0 YAML workflow
sisyphus plan init
sisyphus plan lint .sisyphus/tasks/
sisyphus task continue

# Task navigation
sisyphus task current
sisyphus task next
sisyphus task show <task-id>

# Verification
sisyphus task verify bash
sisyphus task verify status

# Plan visualization
sisyphus plan graph .sisyphus/tasks/ --format ascii
sisyphus plan graph .sisyphus/tasks/ --format mermaid
sisyphus plan graph .sisyphus/tasks/ --format png --output graph.png
```

**Git Management:**
```bash
# Add Sisyphus files to .gitignore
sisyphus ignore

# Show cleanup guide for git history
sisyphus clean-history --dry-run
```

## CONVENTIONS

**Predicted Standard Conventions:**
Python 3.12 project → Expect: PEP 8, type hints, pytest, standard async patterns, ABC for interfaces

**Actual Deviations:**
- **ANN001 enforced:** ALL function parameters MUST have type hints (ruff rule)
- **Protocol > ABC:** Use `typing.Protocol` (PEP 544) with `@runtime_checkable`, NOT Abstract Base Classes
- **anyio > asyncio:** All async uses anyio (`anyio.sleep`, `anyio.create_task_group`), NOT raw asyncio/trio
- **Double quotes only:** Strings MUST use `"` (ruff flake8-quotes enforced)
- **Line length 119:** NOT 88 (Black) or 120 (common)
- **Given-When-Then tests:** Test structure, NOT Arrange-Act-Assert
- **pytest.mark.anyio required:** All async tests need `pytestmark = [pytest.mark.anyio]`
- **Agent.stream() pattern:** Async generator, NOT callback → `async for message in agent.stream()`
- **YAML v3.0 format:** Pydantic models, NOT Markdown or JSON
- **Plan dependencies validated:** Circular deps trigger lint errors
- **No nested imports:** Always top-level, use `if TYPE_CHECKING:` for circular deps

**Import rules:**
```python
from __future__ import annotations  # Always first
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sisyphus_core.core.plans.models import WorkPlan  # Avoid circular imports
```

**Test structure:**
```python
# All imports at top
import pytest

# pytestmark immediately after imports
pytestmark = [pytest.mark.anyio]

# All test functions
async def test_foo__if_bar__returns_baz(): ...

# All fixtures at bottom
@pytest.fixture
def my_fixture(): ...
```

## NOTES

**Critical Non-Obvious Information:**

1. **v3.0 YAML is mandatory**: CLI expects `.sisyphus/tasks/*.yaml` structure with WorkPlan format.

2. **Plan dependencies auto-resolve**: `depends_on: ["plan-foundation"]` → Sisyphus executes `plan-foundation` first, waits for all tasks complete, then moves to dependent plan.

3. **TUI asyncio-only**: Textual limitation. CLI mode supports trio via anyio. Use `--no-tui` if need trio backend.

4. **Status tracking per worktree**: `.sisyphus/status.json` tracks current plan independently per git worktree → parallel development on multiple branches.

5. **Agent Protocol runtime_checkable**: Uses `@runtime_checkable` Protocol → can use `isinstance(obj, Agent)` checks at runtime.

6. **Plan linter checks**:
   - Circular dependencies (A → B → A)
   - Missing plan files referenced in `depends_on`
   - Invalid reference IDs in todos
   - Malformed YAML structure

7. **Graph rendering requires graphviz**: PNG format needs `graphviz` library (dev dependency). ASCII/Mermaid work without.

8. **Legacy converter available**: `sisyphus plan convert-legacy ai-todolist.md` migrates v2.1 Markdown → v3.0 YAML.

9. **No session persistence in v3.0**: Unlike v2.1 `work` command (session resume), v3.0 `task continue` does NOT persist agent session between runs. Each execution starts fresh.

10. **Plan references support inline + URI**: Use `inline: "quick note"` for context or `uri: "https://..."` for external docs. Both can coexist.

11. **Cross-file dependencies**: v3.0 supports splitting plans across multiple files:
   - Use `file:path/to/plan.yaml#plan-id` for direct file references (relative or absolute paths)
   - Use `registry:plan-id` with `.sisyphus/registry.yaml` for central management in large projects
   - PlanLinter validates external dependencies automatically (file existence, plan ID validity, circular deps)
   - Both methods can coexist in the same project
   - File path reference best for 2-5 plan files with direct dependencies
   - Registry reference best for 10+ plan files with complex dependency graphs
   - See `examples/multi-file/` for complete usage examples with backend/frontend split

**Security:**
- No credential validation for Claude/OpenCode APIs
- YAML files world-readable (no encryption)
- Git history cleanup uses `git rebase -i` → destructive, requires force push

**Performance:**
- Textual TUI may lag on large message streams (no pagination)
- Plan linter loads all YAML files in directory → slow for 100+ plans
- No caching for plan validation → re-parses on every `lint` call
