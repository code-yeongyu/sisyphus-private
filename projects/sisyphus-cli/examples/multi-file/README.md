# Multi-File Plan Example

This example demonstrates cross-file dependency management in Sisyphus v3.0.

## Structure

```
multi-file/
├── backend.yaml           # Backend API plan (no dependencies)
├── frontend.yaml          # Frontend plan (depends on backend)
├── .sisyphus/
│   └── registry.yaml      # Global registry for all plans
└── README.md              # This file
```

## Dependency Graph

```
backend-api (backend.yaml)
  └─> frontend-app (frontend.yaml)
```

The frontend plan depends on the backend plan. Sisyphus will:
1. Execute all tasks in `backend-api` first
2. Wait until backend plan completes
3. Automatically start `frontend-app` tasks

## File Path Reference

**frontend.yaml** uses file path reference to declare dependency:

```yaml
work_plans:
  - id: frontend-app
    name: "Frontend Application"
    depends_on:
      - file:backend.yaml#backend-api  # Relative path to backend.yaml
```

The format is: `file:<path-to-yaml>#<plan-id>`

- **Path can be relative** (to current file) or absolute
- **Hash separator** (`#`) separates file path from plan ID
- **Validation**: PlanLinter checks if file exists and plan ID is valid

## Registry Reference (Alternative)

You can also use the global registry for dependency references:

```yaml
work_plans:
  - id: frontend-app
    depends_on:
      - registry:backend-api  # Reference via registry instead of file path
```

The registry (`.sisyphus/registry.yaml`) maps plan IDs to their files:

```yaml
version: "1.0"
plans:
  - file: backend.yaml
    plans:
      - backend-api
  - file: frontend.yaml
    plans:
      - frontend-app
```

## Usage

### Validate Plans

```bash
# Lint individual files
uv run sisyphus plan lint backend.yaml
uv run sisyphus plan lint frontend.yaml

# Lint all plans in directory
uv run sisyphus plan lint .
```

PlanLinter automatically:
- Resolves `file:` references to external YAML files
- Checks if referenced plan IDs exist
- Validates registry.yaml structure (if present)
- Detects circular dependencies across files

### Visualize Dependencies

```bash
# ASCII format (terminal-friendly)
uv run sisyphus plan graph . --format ascii

# Expected output:
# backend-api
#   └─> frontend-app

# Mermaid format (for documentation)
uv run sisyphus plan graph . --format mermaid

# PNG format (requires graphviz)
uv run sisyphus plan graph . --format png --output dependency-graph.png
```

### Execute Tasks

```bash
# Copy to .sisyphus/tasks/ in your project
mkdir -p .sisyphus/tasks
cp backend.yaml frontend.yaml .sisyphus/tasks/
cp -r .sisyphus/registry.yaml .sisyphus/

# Start execution (backend runs first automatically)
uv run sisyphus task continue --execute claude:sonnet
```

Sisyphus will execute plans in dependency order:
1. `backend-api` tasks (1 → 2 → 3)
2. `frontend-app` tasks (1 → 2 → 3)

## When to Use File References vs Registry

### Use File Path Reference (`file:`) when:
- Small projects with 2-5 plan files
- Direct 1-to-1 dependencies
- You want explicit visibility of which file depends on which

### Use Registry Reference (`registry:`) when:
- Large projects with 10+ plan files
- Complex dependency graphs
- You want centralized plan management
- Multiple plans depend on the same external plan

## Key Benefits

✅ **Modularity**: Split large projects into focused, manageable plan files

✅ **Team Collaboration**: Reduce merge conflicts by separating domain plans (backend/frontend/infra)

✅ **Execution Order**: Sisyphus automatically resolves dependencies and executes in correct order

✅ **Validation**: Lint catches broken references before execution

✅ **Flexibility**: Mix file and registry references in the same project

## See Also

- [README.md](../../README.md#cross-file-dependencies) - Full cross-file dependency documentation
- [simple-project.yaml](../simple-project.yaml) - Single-file plan example
- [multi-plan-dependencies.yaml](../multi-plan-dependencies.yaml) - Multi-plan example (same file)
