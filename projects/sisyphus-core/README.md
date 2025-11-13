# Sisyphus Core

Shared core modules for the Sisyphus monorepo - providing common functionality for plan management, agents, utilities, and UI components.

## Overview

`sisyphus-core` is a library package that contains all shared core logic used by other Sisyphus packages (sisyphus-cli, sisyphus-speckit). It provides:

- **Plan Models & Loaders** (`sisyphus_core.core.plans`): YAML v3.0 plan format, loading, and validation
- **Agent Protocol** (`sisyphus_core.agents`): Base agent interface and implementations (Claude, OpenCode)
- **UI Components** (`sisyphus_core.ui`): TUI (Textual) and CLI (Rich) components
- **Utilities** (`sisyphus_core.utils`): Cross-cutting utility functions
- **Plan Management** (`sisyphus_core.core`): Core logic (task manager, status tracking, plan linting, graph rendering)

## Purpose

This package centralizes all domain logic to avoid duplication across sisyphus-cli and sisyphus-speckit. Both CLI packages depend on sisyphus-core and use its exported interfaces.

## Installation

```bash
uv add sisyphus-core
```

Or within a workspace:

```bash
uv sync
```

## Development

```bash
cd projects/sisyphus-core

# Run tests
uv run pytest

# Type checking
uv run basedpyright

# Linting
uv run ruff check
```

## Package Structure

```
sisyphus_core/
├── core/              # Core business logic
│   ├── plans/         # YAML models, loaders, validators
│   ├── status/        # Status tracking
│   ├── task_manager.py # Task navigation
│   ├── plan_linter.py # Plan validation
│   ├── converters/    # Format converters
│   ├── exporters/     # Output exporters
│   └── graph/         # Graph visualization
├── agents/            # Agent implementations
│   ├── base.py        # Agent Protocol
│   ├── claude.py      # ClaudeAgent
│   └── opencode.py    # OpenCodeAgent
├── ui/                # UI layer
│   ├── base.py        # UIProtocol
│   ├── tui/           # Textual TUI
│   ├── cli/           # Rich CLI
│   └── themes.py      # Catppuccin themes
└── utils/             # Utilities
```

## License

Sustainable Use License 1.0
