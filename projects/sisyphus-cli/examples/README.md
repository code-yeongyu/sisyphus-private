# Sisyphus v3.0 Examples

This directory contains example WorkPlan YAML files demonstrating v3.0 features.

## Examples

### 1. `simple-project.yaml`

A basic single-plan project with:
- Inline references
- Nested children tasks
- Bash verification specs

**Use case**: Small projects with straightforward task lists.

**Try it:**
```bash
# Validate the plan
uv run sisyphus plan lint examples/simple-project.yaml

# Export to Markdown
uv run sisyphus plan export examples/simple-project.yaml
```

### 2. `multi-plan-dependencies.yaml`

Multi-plan project demonstrating:
- Plan dependencies (`depends_on`)
- Dependency graph visualization
- Sequential execution across plans

**Use case**: Large projects with multiple phases (foundation → features → testing).

**Try it:**
```bash
# Visualize dependency graph
uv run sisyphus plan graph examples/multi-plan-dependencies.yaml --format ascii

# Expected output:
# plan-foundation
#   └─> plan-main
#       └─> plan-testing

# Check for circular dependencies
uv run sisyphus plan lint examples/multi-plan-dependencies.yaml
```

## Creating Your Own Plans

1. **Start from a template:**
   ```bash
   uv run sisyphus plan init --destination my-project.yaml
   ```

2. **Customize the YAML:**
   - Edit `work_plans[].todos` to add your tasks
   - Set `depends_on` for multi-plan dependencies
   - Add `references` for context
   - Define `verification_spec` for automated checks

3. **Validate:**
   ```bash
   uv run sisyphus plan lint my-project.yaml
   ```

4. **Execute:**
   ```bash
   # Copy to .sisyphus/tasks/
   mkdir -p .sisyphus/tasks
   cp my-project.yaml .sisyphus/tasks/

   # Start execution
   uv run sisyphus task continue --execute claude:sonnet
   ```

## Key v3.0 Features

### Dependencies (`depends_on`)
```yaml
work_plans:
  - id: plan-main
    depends_on: ["plan-foundation"]  # Runs after plan-foundation completes
```

### References (Inline)
```yaml
references:
  - inline: "Use JWT for authentication"
```

### References (External)
```yaml
references:
  - ref_id: "auth_docs"
    uri: "https://jwt.io/introduction"
```

### Children Tasks
```yaml
todos:
  - id: "1"
    title: "Parent task"
    children:
      - id: "1.1"
        title: "Subtask 1"
      - id: "1.2"
        title: "Subtask 2"
```

### Verification Specs
```yaml
verification_spec:
  - type: bash
    description: "Run tests"
    command: "pytest tests/"
    expected_output: "passed"
```

## Migration from v2.1

If you have an old `ai-todolist.md` file:

1. **Convert to v3.0:**
   ```bash
   uv run sisyphus plan convert-legacy ai-todolist.md --output .sisyphus/tasks/main.yaml
   ```

2. **Verify conversion:**
   ```bash
   uv run sisyphus plan lint .sisyphus/tasks/main.yaml
   ```

See `docs/migration-v2-to-v3.md` for detailed migration guide.
