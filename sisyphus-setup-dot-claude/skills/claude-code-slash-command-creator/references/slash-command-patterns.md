# Successful Slash Command Patterns

This document contains proven patterns for creating effective slash commands.

## Pattern 1: Simple Action Command

**Use when**: Command performs a single, straightforward action.

**Structure**:
```markdown
---
allowed-tools: Bash(git:*), Read(*)
description: Create a git commit with conventional commit format
argument-hint: <type> <message>
---

# Claude Command: [Name]

## Usage
/command-name <required-arg> [optional-arg]

## What this command does
[One clear sentence]

## Process
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

**Examples**:
- `/commit <message>` - Git commit creation
- `/create-pr <requirements>` - Pull request creation

---

## Pattern 2: Analysis Command with Options

**Use when**: Command analyzes files/directories with configurable depth.

**Structure**:
```markdown
---
allowed-tools: Read(*), Grep(*), Glob(*), Task(*)
description: Analyze security vulnerabilities in code
argument-hint: <file-or-directory> [--severity=<level>] [--fix]
---

## Process
1. Parse arguments and options
2. Read and analyze target
3. Generate findings report
4. Optionally apply fixes
```

**Examples**:
- `/architect <request> [--thinking=<0-10>]`
- `/list-deadcode [directory] [--language=<lang>]`

---

## Pattern 3: Multi-Phase Complex Command

**Use when**: Command requires multiple distinct phases with agent collaboration.

**Structure**:
```markdown
---
allowed-tools: Task(*), Read(*), Write(*), TodoWrite(*)
---

## Process

### Phase 0: Initialize TODO tracking
Always create TodoWrite to track progress

### Phase 1: [First Phase]
[Detailed steps]

### Phase 2: [Second Phase]
[Detailed steps]

### Phase 3: [Final Phase]
[Completion and validation]
```

**Examples**:
- `/debate <topic>` - Multi-model debate with rounds
- `/rewrite <code>` - Iterative code refinement

---

## Pattern 4: Data Processing Command

**Use when**: Command processes data files with intelligent tool selection.

**Structure**:
```markdown
---
allowed-tools: Read(*), Bash(*)
description: Process data with optimal tool selection
argument-hint: <request> [file] [--output=<format>]
---

## Decision Tree
1. Analyze operation type (filter/join/aggregate)
2. Select optimal tool (DuckDB/Polars)
3. Execute with performance optimization
4. Report metrics
```

**Examples**:
- `/handle-data <request> [file]`

---

## Pattern 5: Project Setup Command

**Use when**: Command creates project structure with dependencies.

**Structure**:
```markdown
---
allowed-tools: Bash(*), Write(*), Read(*), TodoWrite(*)
---

## Process
1. **Environment Validation**
2. **Argument Parsing**
3. **Project Initialization**
4. **Dependency Installation**
5. **Configuration Setup**
6. **Git Initialization** (if needed)
```

**Examples**:
- `/create-python-project [name] [--packages=...]`

---

## Common Antipatterns to Avoid

### ❌ Antipattern 1: Emoji Usage
**Bad**:
```markdown
## Process
1. ✅ Parse arguments
2. 🔍 Analyze code
3. 📝 Generate report
```

**Good**:
```markdown
## Process
1. **Parse Arguments**: Extract and validate inputs
2. **Analyze Code**: Run static analysis
3. **Generate Report**: Create structured output
```

### ❌ Antipattern 2: Including Formatters
**Bad**:
```yaml
allowed-tools: Read(*), Write(*), Bash(yamlfmt:*)
```

**Good**:
```yaml
allowed-tools: Read(*), Write(*)
```

### ❌ Antipattern 3: Vague Descriptions
**Bad**:
```yaml
description: Do stuff with code
argument-hint: <things>
```

**Good**:
```yaml
description: Analyze code complexity and suggest refactoring improvements
argument-hint: <file-path> [--depth=<1-5>] [--focus=<area>]
```

### ❌ Antipattern 4: Missing Error Handling
**Bad**:
```markdown
## Process
1. Read file
2. Process data
3. Output results
```

**Good**:
```markdown
## Process
1. **Validate Inputs**: Check file exists, permissions OK
2. **Read File**: Handle encoding errors, file too large
3. **Process Data**: Validate format, handle malformed data
4. **Output Results**: Check write permissions, confirm success
```

---

## Best Practices

### 1. Frontmatter Completeness
Always include all required fields:
- `allowed-tools` - Minimal necessary permissions
- `description` - Specific, searchable description
- `argument-hint` - Clear format with required/optional indicators

### 2. Clear Process Steps
Use imperative verbs and numbered steps:
```markdown
## Process
1. **Validate Environment**: Check prerequisites
2. **Parse Arguments**: Extract parameters
3. **Execute Task**: Perform main operation
4. **Verify Results**: Confirm success
```

### 3. Tool Permissions
Apply principle of least privilege:
```yaml
# Too broad
allowed-tools: Bash(*)

# Better
allowed-tools: Bash(git:*), Bash(npm:*), Bash(python:*)
```

### 4. Language Consistency
Unless `--language` parameter explicitly specified, ALL content in English:
- Section headers
- Instructions
- Examples
- Error messages

### 5. Argument Hints Format
Use standard conventions:
- `<required>` - Angle brackets for required args
- `[optional]` - Square brackets for optional args
- `|` - Pipe for alternatives
- `...` - Ellipsis for variable args

Examples:
```
<action> <target> [--verbose]
add <item> | remove <item> | list
<command-name> <"description"> [--type=<project|user>]
```
