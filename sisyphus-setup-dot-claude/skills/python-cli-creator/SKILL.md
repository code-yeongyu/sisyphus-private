---
name: python-cli-creator
description: Create beautiful, modern Python CLI applications using Typer and Rich. Activate when building command-line tools, adding terminal UI features, implementing CLI commands, or enhancing existing CLIs with progress bars, tables, and interactive prompts.
---

# Python CLI Creator (Typer + Rich)

Expert guide for creating beautiful, modern Python CLI applications.

## Philosophy

**Typer** handles CLI structure, argument parsing, and command organization.
**Rich** provides beautiful terminal output, formatting, and interactive displays.

Together, they create professional-grade CLI applications with minimal boilerplate.

## Quick Start

Create a new CLI project instantly:

```bash
# Use the initialization script
uv run scripts/init_cli.py my_awesome_cli

# Or manually start with this template:
```

```python
import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer()
console = Console()

@app.command()
def hello(name: str = typer.Option("World", help="Person to greet")):
    """Greet someone with style!"""
    console.print(Panel(
        f"[bold magenta]Hello, {name}![/bold magenta]",
        title="Greeting",
        border_style="green"
    ))

if __name__ == "__main__":
    app()
```

## Core Workflow

### 1. Choose Your Patterns

Refer to **[references/essential-patterns.md](references/essential-patterns.md)** for 14 core patterns:

1. Multi-command structure (sub-commands)
2. Arguments and options (required, optional, validation)
3. Progress bars (long-running tasks)
4. Tables (structured data display)
5. Error handling (panels, exit codes)
6. Interactive prompts (user input)
7. Status and spinners (ongoing operations)
8. Live updates (real-time dashboards)
9. Rich logging (structured logs)
10. Version callbacks (--version flag)
11. Exception handling (beautiful tracebacks)
12. Configuration management (file handling)
13. Tree display (hierarchical data)
14. Markdown rendering (documentation)

### 2. Implement Features

Start simple, then progressively enhance:

1. **Single command** → Basic functionality
2. **Add Rich console** → Beautiful output
3. **Structure with sub-commands** → As complexity grows
4. **Implement error handling** → With panels
5. **Add progress indicators** → For long operations
6. **Create consistent styling** → With themes
7. **Write tests** → Using CliRunner
8. **Package and distribute** → Via PyPI

### 3. Advanced Features

For advanced use cases, see **[references/advanced-features.md](references/advanced-features.md)**:

- Testing with CliRunner and Rich output
- Packaging with modern pyproject.toml
- Performance optimization (lazy imports, async)
- Advanced patterns (retry logic, plugins, signals)
- Consistent styling system

### 4. Real-World Examples

Study complete production CLIs in **[references/real-world-examples.md](references/real-world-examples.md)**:

- Database migration tool
- File processing CLI
- API client
- Build tool
- System monitor
- Code generator

### 5. Troubleshooting

When issues arise, consult **[references/troubleshooting.md](references/troubleshooting.md)**:

- Display issues (colors, Unicode, progress bars)
- Typer parameter problems
- Rich rendering issues
- Testing challenges
- Packaging errors
- Performance bottlenecks

## Project Initialization

Use the included `scripts/init_cli.py` to scaffold a complete CLI project:

```bash
# Create new project
uv run scripts/init_cli.py my_cli

# With custom settings
uv run scripts/init_cli.py my_cli \
    --path ~/projects \
    --author-name "Your Name" \
    --author-email "you@example.com"
```

This creates a complete project structure with:
- Main CLI application with example commands
- Rich-themed output utilities
- Test suite with pytest
- Modern pyproject.toml configuration
- README and .gitignore

## Essential Patterns Reference

### When to Use Which Pattern

**Single command CLI** → Use basic `@app.command()` pattern
**Multiple commands** → Use `app.add_typer()` for sub-command groups
**Long operations** → Use `Progress()` with progress bars
**Data display** → Use `Table()` for structured output
**User interaction** → Use `Prompt.ask()` or `Confirm.ask()`
**Dangerous operations** → Use `Panel()` with confirmation
**Real-time updates** → Use `Live()` for dashboards
**File processing** → Combine `Progress()` + error handling

### Common Combinations

**Database CLI** → Multi-command + Tables + Progress
**Build Tool** → Status spinners + Error panels + Exit codes
**API Client** → Interactive prompts + Progress + Error handling
**File Processor** → Progress bars + Error recovery + Statistics
**System Monitor** → Live updates + Tables + Refresh loops

## Best Practices Checklist

- ✅ Use type hints for all Typer parameters
- ✅ Provide help text for commands and options
- ✅ Use Rich for all output (no plain print)
- ✅ Implement proper error handling with exit codes
- ✅ Create consistent styling/theme
- ✅ Add `--version` flag
- ✅ Write tests using `CliRunner`
- ✅ Document with docstrings
- ✅ Use sub-commands for complex CLIs
- ✅ Keep business logic separate from CLI code
- ✅ Handle keyboard interrupts gracefully

## Implementation Strategy

1. **Start simple** - Single command with basic functionality
2. **Add Rich** - Beautiful output for user experience
3. **Structure commands** - Organize with sub-commands as needed
4. **Error handling** - Professional error display and recovery
5. **Progress tracking** - Visual feedback for long operations
6. **Consistent styling** - Theme and helper functions
7. **Testing** - Comprehensive test suite
8. **Distribution** - Package via PyPI

Remember: Start with basic functionality, then progressively enhance with Rich's powerful features!

## Resources

### Official Documentation

- **Typer**: https://typer.tiangolo.com/
- **Rich**: https://rich.readthedocs.io/

### Reference Files

- [Essential Patterns](references/essential-patterns.md) - 14 core patterns with code examples
- [Advanced Features](references/advanced-features.md) - Testing, packaging, performance
- [Real-World Examples](references/real-world-examples.md) - Complete production CLIs
- [Troubleshooting](references/troubleshooting.md) - Common issues and solutions

### Community

- Typer GitHub: https://github.com/tiangolo/typer
- Rich GitHub: https://github.com/Textualize/rich
