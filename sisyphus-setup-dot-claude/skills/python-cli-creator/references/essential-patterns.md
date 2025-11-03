# Essential Patterns for Python CLI (Typer + Rich)

14 core patterns that cover 90% of CLI development scenarios.

## Table of Contents

1. [Application Structure (Multi-Command)](#1-application-structure-multi-command)
2. [Arguments and Options](#2-arguments-and-options)
3. [Progress Bars](#3-progress-bars-long-running-tasks)
4. [Beautiful Tables](#4-beautiful-tables)
5. [Error Handling](#5-error-handling-with-rich-panels)
6. [Interactive Prompts](#6-interactive-prompts)
7. [Status and Spinners](#7-status-and-spinners)
8. [Live Updates](#8-live-updates-real-time-display)
9. [Rich Logging](#9-rich-logging)
10. [Version Callback](#10-version-callback)
11. [Exception Handling](#11-exception-handling-with-rich-traceback)
12. [Configuration Management](#12-configuration-management-pattern)
13. [Tree Display](#13-tree-display-file-system)
14. [Markdown Rendering](#14-markdown-rendering)

---

## 1. Application Structure (Multi-Command)

For CLIs with multiple sub-commands, organize using Typer groups:

```python
import typer
from rich.console import Console

# Main app and console
app = typer.Typer()
console = Console()

# Sub-command groups
db_app = typer.Typer()
user_app = typer.Typer()

@db_app.command()
def init():
    """Initialize database"""
    console.print("[green]Database initialized![/green]")

@db_app.command()
def migrate():
    """Run migrations"""
    console.print("[yellow]Running migrations...[/yellow]")

@user_app.command()
def create(name: str):
    """Create a new user"""
    console.print(f"[blue]User '{name}' created![/blue]")

@user_app.command()
def delete(name: str):
    """Delete a user"""
    console.print(f"[red]User '{name}' deleted![/red]")

# Register sub-commands
app.add_typer(db_app, name="db", help="Database commands")
app.add_typer(user_app, name="user", help="User management")

if __name__ == "__main__":
    app()
```

**Usage:**
```bash
python app.py db init
python app.py user create Alice
```

---

## 2. Arguments and Options

Complete parameter types and validation:

```python
from typing import Optional, List
import typer

@app.command()
def process(
    # Required argument
    input_file: str,

    # Optional argument with default
    output_file: str = "output.txt",

    # Required option (use ... as default)
    api_key: str = typer.Option(..., help="API key (required)"),

    # Optional option with default
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),

    # Multiple values
    tags: Optional[List[str]] = typer.Option(None, help="Tags to apply"),

    # Integer with validation
    count: int = typer.Option(10, min=1, max=100, help="Number of items")
):
    """Process files with options"""
    console.print(f"Processing {input_file} -> {output_file}")
    if verbose:
        console.print(f"[dim]Tags: {tags}, Count: {count}[/dim]")
```

---

## 3. Progress Bars (Long-Running Tasks)

Show progress for operations that take time:

```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

@app.command()
def download():
    """Download files with progress"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:

        task1 = progress.add_task("[cyan]Downloading...", total=100)
        task2 = progress.add_task("[magenta]Processing...", total=100)

        import time
        while not progress.finished:
            progress.update(task1, advance=0.9)
            progress.update(task2, advance=0.5)
            time.sleep(0.02)

    console.print("[green]✓[/green] Download complete!")
```

---

## 4. Beautiful Tables

Display structured data elegantly:

```python
from rich.table import Table

@app.command()
def list_users():
    """Display users in a table"""
    table = Table(title="Active Users", show_header=True, header_style="bold magenta")

    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Status", justify="center")

    # Sample data
    users = [
        ("1", "Alice", "alice@example.com", "✓ Active"),
        ("2", "Bob", "bob@example.com", "✓ Active"),
        ("3", "Charlie", "charlie@example.com", "⏸ Inactive"),
    ]

    for user_id, name, email, status in users:
        table.add_row(user_id, name, email, status)

    console.print(table)
```

---

## 5. Error Handling with Rich Panels

Professional error display with context:

```python
from rich.panel import Panel

@app.command()
def dangerous_operation(force: bool = typer.Option(False, help="Force operation")):
    """A potentially dangerous operation"""

    if not force:
        console.print(Panel(
            "[red bold]ERROR:[/red bold] This is a dangerous operation!\n"
            "Use [cyan]--force[/cyan] to proceed.",
            title="⚠ Warning",
            border_style="red"
        ))
        raise typer.Exit(code=1)

    try:
        # Perform operation
        console.print("[green]Operation completed successfully![/green]")
    except Exception as e:
        console.print(Panel(
            f"[red]Error: {str(e)}[/red]",
            title="❌ Operation Failed",
            border_style="red"
        ))
        raise typer.Exit(code=1)
```

---

## 6. Interactive Prompts

Get user input with validation:

```python
from rich.prompt import Prompt, Confirm, IntPrompt

@app.command()
def configure():
    """Interactive configuration"""

    # Text prompt with default
    name = Prompt.ask("Enter your [cyan]name[/cyan]", default="User")

    # Integer prompt with validation
    age = IntPrompt.ask("Enter your [yellow]age[/yellow]", default=25)

    # Choices
    theme = Prompt.ask(
        "Choose a [magenta]theme[/magenta]",
        choices=["dark", "light", "auto"],
        default="dark"
    )

    # Confirmation
    confirm = Confirm.ask("Save configuration?")

    if confirm:
        console.print(f"[green]✓[/green] Configuration saved for {name}")
    else:
        console.print("[yellow]Configuration cancelled[/yellow]")
```

---

## 7. Status and Spinners

Show ongoing operations without progress tracking:

```python
from rich.status import Status
import time

@app.command()
def deploy():
    """Deploy application with status updates"""

    with console.status("[bold green]Deploying...", spinner="dots") as status:
        time.sleep(2)
        console.log("✓ Building application")

        status.update("[bold yellow]Uploading assets...")
        time.sleep(2)
        console.log("✓ Assets uploaded")

        status.update("[bold blue]Restarting services...")
        time.sleep(2)
        console.log("✓ Services restarted")

    console.print("[bold green]🚀 Deployment complete![/bold green]")
```

---

## 8. Live Updates (Real-time Display)

Update display in real-time (dashboards, monitors):

```python
from rich.live import Live
from rich.table import Table
import time

@app.command()
def monitor():
    """Monitor system with live updates"""

    def generate_table():
        table = Table(title="System Monitor")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("CPU %", justify="right", style="green")

        # This would normally fetch real data
        import random
        table.add_row("API", "Running", f"{random.randint(10, 50)}%")
        table.add_row("Database", "Running", f"{random.randint(5, 30)}%")
        table.add_row("Cache", "Running", f"{random.randint(1, 10)}%")

        return table

    with Live(generate_table(), refresh_per_second=4) as live:
        for _ in range(20):
            time.sleep(0.4)
            live.update(generate_table())
```

---

## 9. Rich Logging

Replace print() with beautiful structured logs:

```python
import logging
from rich.logging import RichHandler

# Setup rich logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")

@app.command()
def process_data():
    """Process data with rich logging"""
    log.info("Starting data processing")
    log.warning("Low memory detected")
    log.error("Failed to connect to database")
    log.debug("Debug information")
```

---

## 10. Version Callback

Standard --version flag implementation:

```python
def version_callback(value: bool):
    """Show version and exit"""
    if value:
        console.print("MyApp [bold cyan]v1.0.0[/bold cyan]")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True
    )
):
    """My Awesome CLI Application"""
    pass
```

---

## 11. Exception Handling with Rich Traceback

Beautiful, informative error traces:

```python
from rich.traceback import install

# Install rich traceback handler (do this at the top of your file)
install(show_locals=True)

@app.command()
def risky_operation():
    """Operation that might fail"""
    try:
        # Your code here
        result = 1 / 0
    except Exception:
        console.print_exception(show_locals=True)
        raise typer.Exit(code=1)
```

---

## 12. Configuration Management Pattern

Read and display config files with syntax highlighting:

```python
from pathlib import Path
from rich.syntax import Syntax
import json

@app.command()
def show_config(
    config_path: Path = typer.Option(
        Path("config.json"),
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to config file"
    )
):
    """Display configuration file with syntax highlighting"""

    content = config_path.read_text()

    # Determine file type
    suffix = config_path.suffix.lstrip('.')

    syntax = Syntax(
        content,
        suffix or "json",
        theme="monokai",
        line_numbers=True
    )

    console.print(syntax)
```

---

## 13. Tree Display (File System)

Show hierarchical structures beautifully:

```python
from rich.tree import Tree

@app.command()
def show_structure():
    """Display project structure"""

    tree = Tree("📁 [bold cyan]my-project[/bold cyan]")

    src = tree.add("📁 src")
    src.add("📄 main.py")
    src.add("📄 utils.py")

    tests = tree.add("📁 tests")
    tests.add("📄 test_main.py")

    tree.add("📄 README.md")
    tree.add("📄 requirements.txt")

    console.print(tree)
```

---

## 14. Markdown Rendering

Display formatted documentation in terminal:

```python
from rich.markdown import Markdown

@app.command()
def show_docs():
    """Display documentation in markdown"""

    markdown_text = """
# MyApp Documentation

## Features

- Fast and efficient
- Beautiful CLI interface
- Easy to use

## Installation

```bash
pip install myapp
```

## Quick Start

Run `myapp --help` to get started!
"""

    md = Markdown(markdown_text)
    console.print(md)
```

---

## Complete Project Structure

Recommended structure for production CLIs:

```
mycli/
├── __init__.py
├── __main__.py          # Entry point
├── cli.py               # Main CLI logic
├── commands/
│   ├── __init__.py
│   ├── db.py           # Database commands
│   └── user.py         # User commands
├── utils/
│   ├── __init__.py
│   ├── output.py       # Rich console & styles
│   └── config.py       # Configuration handling
├── tests/
│   ├── __init__.py
│   └── test_cli.py
├── pyproject.toml      # or setup.py
└── README.md
```

**cli.py:**
```python
import typer
from mycli.commands import db, user
from mycli.utils.output import console

app = typer.Typer(
    name="mycli",
    help="My Awesome CLI Application",
    add_completion=True,
)

# Register sub-commands
app.add_typer(db.app, name="db", help="Database operations")
app.add_typer(user.app, name="user", help="User management")

@app.callback()
def main():
    """Main callback"""
    pass

if __name__ == "__main__":
    app()
```

**utils/output.py:**
```python
from rich.console import Console
from rich.theme import Theme

# Custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

console = Console(theme=custom_theme)

def print_header(text: str):
    """Print styled header"""
    console.print(f"\n[bold white on blue] {text} [/bold white on blue]\n")

def print_success(text: str):
    console.print(f"[success]✓[/success] {text}")

def print_error(text: str):
    console.print(f"[error]✗[/error] {text}")

def print_warning(text: str):
    console.print(f"[warning]⚠[/warning] {text}")
```
