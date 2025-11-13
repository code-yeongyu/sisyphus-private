# sisyphus-speckit

Plan and task specification tools for the Sisyphus multi-agent orchestration system.

## Overview

`sisyphus-speckit` provides specialized commands for managing work plans and tasks:

- **plan** commands: Initialize, lint, visualize, and export YAML work plans
- **task** commands: Navigate and execute tasks from active plans

This package depends on `sisyphus-core`, which provides the shared core logic (models, agents, utilities).

## Installation

```bash
pip install sisyphus-speckit
```

## Quick Start

### Plan Management

```bash
# Initialize a new work plan
sisyphus-speckit plan init .sisyphus/tasks/my-project.yaml

# Validate plan structure
sisyphus-speckit plan lint .sisyphus/tasks/

# Visualize dependencies
sisyphus-speckit plan graph .sisyphus/tasks/ --format mermaid

# Export plan to Markdown
sisyphus-speckit plan export .sisyphus/tasks/my-project.yaml --output plan.md
```

### Task Execution

```bash
# Get current task
sisyphus-speckit task current

# Continue with next task
sisyphus-speckit task continue

# Show task details
sisyphus-speckit task show <task-id>

# Verify task completion
sisyphus-speckit task verify bash
sisyphus-speckit task verify manual
```

## Architecture

sisyphus-speckit is part of a 3-package monorepo structure:

- **sisyphus-core**: Shared core modules (models, agents, utilities, UI)
- **sisyphus-cli**: Work execution commands (`work`, `ignore`, `reset`, `clean-history`)
- **sisyphus-speckit**: Plan and task specification (`plan`, `task`)

## Commands

### plan

- `plan init`: Create new YAML work plan
- `plan lint`: Validate plan structure and dependencies
- `plan graph`: Visualize task dependency graph
- `plan export`: Export plan to Markdown format
- `plan convert-legacy`: Convert v2.1 Markdown plans to v3.0 YAML

### task

- `task current`: Display current task
- `task continue`: Advance to next task
- `task next`: Show next available task
- `task show`: Display task details
- `task verify`: Run verification checks (bash, llm, manual)

## Documentation

See the root `README.md` for complete documentation and examples.

## License

Sustainable Use License 1.0
