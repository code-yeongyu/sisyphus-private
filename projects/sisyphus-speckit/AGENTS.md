# PROJECT KNOWLEDGE BASE

**Generated:** 2025-11-18 17:26:52 KST
**Commit:** b90db35
**Branch:** master
**Repo:** https://github.com/code-yeongyu/sisyphus-private.git

## OVERVIEW

Python 3.12+ CLI package → Plan + task specification tools for Sisyphus orchestration

**Purpose:** Manage YAML work plans and navigate tasks
- `plan` commands → init, lint, graph, export
- `task` commands → current, continue, next, verify

Part of 3-package monorepo:
- sisyphus-core → shared logic (models, agents, UI)
- sisyphus-cli → work execution
- **sisyphus-speckit** → plan/task management (this package)

## TECH STACK

**Language:** Python 3.12+
**CLI:** Typer 0.15+ → command routing
**Output:** Rich 13+ → formatted console
**Core:** sisyphus-core ≥0.1.0 → shared models, agents, utilities

**Dev Dependencies:**
- graphviz 0.21+ → PNG graph rendering

## STRUCTURE

```
sisyphus-speckit/
├── sisyphus_speckit/
│   ├── cli.py             # Typer app entry point
│   ├── plan/              # Plan management commands
│   │   ├── init.py        # Create new YAML plan
│   │   ├── lint.py        # Validate structure
│   │   ├── graph.py       # Visualize dependencies
│   │   ├── export.py      # YAML → Markdown
│   │   └── convert.py     # v2.1 → v3.0 migration
│   └── task/              # Task execution commands
│       ├── current.py     # Display current task
│       ├── continue_.py   # Advance to next task
│       ├── next.py        # Show next available
│       ├── show.py        # Task details
│       └── verify.py      # Run verification checks
└── tests/                 # Test suite
```

## COMMANDS

**plan:**
```bash
sisyphus-speckit plan init <path>              # Create YAML plan
sisyphus-speckit plan lint <dir>               # Validate plans
sisyphus-speckit plan graph <dir> [--format]   # Visualize (mermaid/ascii/png)
sisyphus-speckit plan export <path> [--output] # YAML → Markdown
sisyphus-speckit plan convert-legacy <md>      # v2.1 → v3.0
```

**task:**
```bash
sisyphus-speckit task current                  # Show current task
sisyphus-speckit task continue                 # Advance to next
sisyphus-speckit task next                     # Show next task
sisyphus-speckit task show <task-id>           # Task details
sisyphus-speckit task verify bash|llm|manual   # Run checks
```

## NOTES

**Separation from sisyphus-cli:**
- sisyphus-cli → work execution (`work`, `ignore`, `reset`, `clean-history`)
- sisyphus-speckit → plan/task specification (this package)
- Both depend on sisyphus-core for shared logic

**Entry point:** `sisyphus-speckit` CLI registered via `project.scripts`

**Conventions:** Inherits from sisyphus-core
- Protocol-based design
- Type hints required (ANN001)
- Double quotes only
- Line length 119
- Given-When-Then tests
