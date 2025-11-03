# Claude Code Documentation References

Essential documentation for understanding slash commands and Claude Code features.

## Primary References

### Slash Commands
- **URL**: https://docs.claude.com/en/docs/claude-code/slash-commands.md
- **When to read**: Always read this first when creating a slash command
- **Contains**:
  - How slash commands work
  - Frontmatter structure
  - allowed-tools syntax
  - Best practices

### Common Workflows - Slash Commands
- **URL**: https://docs.claude.com/en/docs/claude-code/common-workflows.md
- **Section**: ## Create custom slash commands
- **When to read**: When understanding the user workflow for creating commands
- **Contains**:
  - User-facing guide to slash command creation
  - Examples of when to create custom commands
  - Integration with existing workflows

## Tool Permissions

### Glob Patterns in allowed-tools
Commands support wildcard permissions:
```yaml
# Allow all Read operations
allowed-tools: Read(*)

# Allow specific git operations
allowed-tools: Bash(git:*)

# Allow specific operations only
allowed-tools: Bash(git status:*), Bash(git diff:*)

# Multiple tool types
allowed-tools: Read(*), Write(*), Bash(python:*), Glob(*)
```

### Principle of Least Privilege
Only grant permissions actually needed:
```yaml
# Bad - too permissive
allowed-tools: Bash(*)

# Good - specific permissions
allowed-tools: Bash(git:*), Bash(npm install:*), Read(*), Write(*)
```

## Frontmatter Fields

### Required Fields
1. **allowed-tools**: List of tool permissions
2. **description**: Clear description of command purpose
3. **argument-hint**: Expected argument format

### Optional Fields
4. **model**: Specific model to use (e.g., "haiku", "sonnet", "opus")

### Example Complete Frontmatter
```yaml
---
allowed-tools: Read(*), Write(*), Grep(*), Glob(*)
description: Analyze code complexity and suggest improvements
argument-hint: <file-path> [--depth=<1-5>] [--focus=<area>]
model: opus
---
```

## Slash Command Execution Model

### How Slash Commands Expand
When a user types `/my-command arg1 arg2`, Claude Code:
1. Finds `my-command.md` in `.claude/commands/` directories
2. Loads the frontmatter metadata
3. Expands the entire SKILL.md content into the conversation
4. Processes the expanded prompt as if the user typed it
5. Executes using only the tools listed in `allowed-tools`

### Variable Substitution
The command can access arguments via `$ARGUMENTS`:
```markdown
## Process
1. Parse `$ARGUMENTS` to extract parameters
2. Process based on extracted values
```

Example:
```
User: /analyze-code src/main.py --depth=3
$ARGUMENTS = "src/main.py --depth=3"
```

## Directory Structure

### User-level Commands
```
~/.claude/
└── commands/
    ├── my-command.md
    └── another-command.md
```
- Available globally across all projects
- User-specific customizations

### Project-level Commands
```
/project-root/
└── .claude/
    └── commands/
        ├── project-command.md
        └── team-command.md
```
- Available only within the project
- Can be version-controlled with the project
- Team-wide standardization

## Command Naming Conventions

### Verb-Noun Format (Preferred)
Use imperative verb + noun for action-oriented commands:
- ✅ `analyze-code`
- ✅ `generate-tests`
- ✅ `review-pull`
- ✅ `create-docs`
- ✅ `handle-data`

### Avoid Noun-Agent Format
Don't use nouns describing agents or tools:
- ❌ `code-analyzer`
- ❌ `test-generator`
- ❌ `pull-reviewer`
- ❌ `docs-creator`
- ❌ `data-handler`

### Reasoning
Commands are actions that Claude performs, not tools that exist independently. The verb-noun format makes the command's purpose immediately clear.

## Language Settings

### Default Language: English
Unless `--language` parameter is explicitly provided, ALL content must be in English:
- Section headers
- Instructions
- Error messages
- Examples

### Supporting Multiple Languages
Commands can support language parameters:
```yaml
argument-hint: <command-name> <"purpose"> [--language=<lang>]
```

Then in the process:
```markdown
## Process
1. **Parse Language**: Extract `--language` parameter
   - Default: English
   - Supported: ANY language (korean, japanese, chinese, etc.)
2. **Apply Language**: Generate all content in specified language
```

## Advanced Features

### Sequential Thinking Integration
For complex analysis tasks:
```markdown
## Process
1. **Initial Analysis**: Think deeply about the problem
2. **Sequential Thinking**: Use mcp__sequential-thinking__process_thought
   - Each thought should expand on previous insights
   - Process at least 20-50 thoughts for complex tasks
3. **Synthesis**: Generate summary with mcp__sequential-thinking__generate_summary
```

### Agent Collaboration
For tasks requiring specialized expertise:
```markdown
## Process
1. **Analysis Phase**: Perform initial analysis
2. **Expert Review**: Call Task tool with specialized agent
   - Use code-reviewer for code quality
   - Use prompt-engineer for prompt review
3. **Iteration**: Implement feedback and re-review
```

### Progressive Disclosure
For commands with optional complexity:
```markdown
## Process
1. **Quick Mode** (default): Fast, simple execution
2. **Deep Mode** (--deep flag): Comprehensive analysis
   - Load additional references
   - Perform sequential thinking
   - Generate detailed reports
```

## Quality Indicators

A well-designed slash command should:
- ✅ Have clear, specific description (not generic)
- ✅ Use minimal necessary tool permissions
- ✅ Provide structured, step-by-step process
- ✅ Include error handling and validation
- ✅ Define clear output format
- ✅ Support common variations through flags
- ✅ Avoid emojis (use **bold** or UPPERCASE)
- ✅ Be concise (avoid token bloat)
- ✅ Have accurate argument hints
- ✅ Default to English unless specified otherwise
