# Advanced Features

Deep dive into testing, packaging, performance optimization, and advanced patterns.

## Table of Contents

1. [Testing Patterns](#testing-patterns)
2. [Packaging and Distribution](#packaging-and-distribution)
3. [Performance Optimization](#performance-optimization)
4. [Advanced CLI Patterns](#advanced-cli-patterns)
5. [Styling System](#styling-system)

---

## Testing Patterns

### Basic Testing with CliRunner

```python
# tests/test_cli.py
from typer.testing import CliRunner
from mycli.cli import app

runner = CliRunner()

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "My Awesome CLI Application" in result.stdout

def test_command():
    result = runner.invoke(app, ["user", "create", "Alice"])
    assert result.exit_code == 0
    assert "created" in result.stdout.lower()

def test_error_handling():
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0
```

### Testing Rich Output

```python
from rich.console import Console
import pytest

def test_rich_output():
    """Test Rich formatted output"""
    console = Console()

    # Capture output
    with console.capture() as capture:
        console.print("[bold]Test[/bold]")

    output = capture.get()
    assert "Test" in output

def test_table_output():
    """Test table rendering"""
    from rich.table import Table

    console = Console()
    table = Table()
    table.add_column("Name")
    table.add_row("Alice")

    with console.capture() as capture:
        console.print(table)

    output = capture.get()
    assert "Alice" in output
```

### Testing Interactive Prompts

```python
def test_interactive_command():
    """Test command with user input"""
    result = runner.invoke(app, ["configure"], input="John\n30\ndark\ny\n")
    assert result.exit_code == 0
    assert "Configuration saved" in result.stdout
```

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock

def test_api_call():
    """Test command that makes API calls"""
    with patch('mycli.api.fetch_data') as mock_fetch:
        mock_fetch.return_value = {"status": "success"}

        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0
        mock_fetch.assert_called_once()
```

### Testing File Operations

```python
import tempfile
from pathlib import Path

def test_file_processing():
    """Test command that processes files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = Path(tmpdir) / "input.txt"
        test_file.write_text("test content")

        # Run command
        result = runner.invoke(app, ["process", str(test_file)])
        assert result.exit_code == 0

        # Verify output
        output_file = Path(tmpdir) / "output.txt"
        assert output_file.exists()
```

### Coverage and CI Integration

```bash
# Install coverage
pip install pytest-cov

# Run with coverage
pytest --cov=mycli --cov-report=html --cov-report=term

# CI configuration (.github/workflows/test.yml)
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=mycli
```

---

## Packaging and Distribution

### Modern pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mycli"
version = "0.1.0"
description = "My Awesome CLI Application"
readme = "README.md"
authors = [{name = "Your Name", email = "you@example.com"}]
license = {text = "MIT"}
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/mycli"
Documentation = "https://mycli.readthedocs.io"
Repository = "https://github.com/yourusername/mycli"
Changelog = "https://github.com/yourusername/mycli/releases"

[project.scripts]
mycli = "mycli.cli:app"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["mycli*"]

[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']

[tool.ruff]
line-length = 88
target-version = "py38"
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Building and Publishing

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Check distribution
twine check dist/*

# Upload to TestPyPI (test first!)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### Development Installation

```bash
# Install in editable mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install from git (for users)
pip install git+https://github.com/yourusername/mycli.git
```

### Version Management

```python
# mycli/__init__.py
__version__ = "0.1.0"

# mycli/cli.py
from mycli import __version__

def version_callback(value: bool):
    if value:
        console.print(f"mycli version [cyan]{__version__}[/cyan]")
        raise typer.Exit()
```

---

## Performance Optimization

### 1. Lazy Imports

Load heavy modules only when needed:

```python
@app.command()
def analyze():
    """Analyze data (lazy import pandas)"""
    # Import only when command runs
    import pandas as pd
    import numpy as np

    # Your analysis code
    df = pd.DataFrame({"col": [1, 2, 3]})
    console.print(f"Processed {len(df)} rows")
```

### 2. Disable Unused Features

```python
app = typer.Typer(
    add_completion=False,      # Disable shell completion if not needed
    rich_markup_mode=None,     # Disable Rich markup if using plain text
    pretty_exceptions_enable=False,  # Disable if using custom error handling
)
```

### 3. Reuse Console Instance

```python
# At module level (not inside functions)
from rich.console import Console

console = Console()  # Create once

# Use throughout your app
@app.command()
def cmd1():
    console.print("Command 1")

@app.command()
def cmd2():
    console.print("Command 2")
```

### 4. Efficient Progress Tracking

```python
from rich.progress import Progress

@app.command()
def process_files(files: List[Path]):
    """Process multiple files efficiently"""

    with Progress() as progress:
        task = progress.add_task("Processing...", total=len(files))

        for file in files:
            # Process file
            process_single_file(file)

            # Update progress (batched)
            progress.update(task, advance=1)
```

### 5. Async Operations

```python
import asyncio
from typing import List

@app.command()
def fetch_all(urls: List[str]):
    """Fetch multiple URLs concurrently"""

    async def fetch(url: str):
        # Async HTTP request
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    async def main():
        tasks = [fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

    results = asyncio.run(main())
    console.print(f"Fetched {len(results)} URLs")
```

---

## Advanced CLI Patterns

### Confirmation Before Dangerous Operations

```python
from rich.prompt import Confirm

@app.command()
def delete_all():
    """Delete all data (requires confirmation)"""
    if not Confirm.ask("[red]Delete all data? This cannot be undone![/red]"):
        console.print("[yellow]Cancelled[/yellow]")
        raise typer.Exit()

    # Proceed with deletion
    console.print("[green]All data deleted[/green]")
```

### Retry Logic with Progress

```python
from rich.progress import track
import time

@app.command()
def retry_operation():
    """Retry failed operations"""
    max_retries = 3

    for attempt in track(range(max_retries), description="Retrying..."):
        try:
            # Your operation
            risky_operation()
            console.print("[green]Success![/green]")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                console.print(f"[error]Failed after {max_retries} attempts[/error]")
                raise typer.Exit(1)
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Multiple Progress Tasks

```python
from rich.progress import Progress

@app.command()
def multi_task():
    """Handle multiple simultaneous tasks"""

    with Progress() as progress:
        download = progress.add_task("[cyan]Download", total=1000)
        process = progress.add_task("[magenta]Process", total=1000)
        upload = progress.add_task("[green]Upload", total=1000)

        # Update as needed
        for i in range(1000):
            progress.update(download, advance=1)
            if i > 500:
                progress.update(process, advance=1)
            if i > 750:
                progress.update(upload, advance=1)
```

### Context Managers for Cleanup

```python
from contextlib import contextmanager

@contextmanager
def temporary_config(config_path: Path):
    """Temporarily modify config and restore"""
    # Backup
    original = config_path.read_text()

    try:
        yield config_path
    finally:
        # Restore
        config_path.write_text(original)

@app.command()
def test_config():
    """Test with temporary config"""
    with temporary_config(Path("config.json")) as config:
        # Modify config
        config.write_text('{"test": true}')

        # Run tests
        run_tests()

    # Config automatically restored
```

### Signal Handling

```python
import signal
import sys

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    console.print("\n[yellow]Operation cancelled by user[/yellow]")
    sys.exit(0)

@app.command()
def long_running():
    """Long-running operation with graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)

    console.print("Press Ctrl+C to cancel...")

    with Progress() as progress:
        task = progress.add_task("Processing...", total=100)

        for i in range(100):
            time.sleep(0.1)
            progress.update(task, advance=1)
```

### Plugin System

```python
from importlib import import_module
from pathlib import Path

@app.command()
def load_plugins():
    """Load and execute plugins"""
    plugin_dir = Path("plugins")

    for plugin_file in plugin_dir.glob("*.py"):
        module_name = plugin_file.stem

        try:
            module = import_module(f"plugins.{module_name}")

            if hasattr(module, "run"):
                console.print(f"[cyan]Running plugin: {module_name}[/cyan]")
                module.run()
        except Exception as e:
            console.print(f"[error]Plugin {module_name} failed: {e}[/error]")
```

---

## Styling System

### Consistent Theme Across Application

```python
# utils/styles.py
from rich.console import Console
from rich.theme import Theme

THEME = Theme({
    "primary": "bold cyan",
    "secondary": "bold magenta",
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "bold blue",
    "muted": "dim",
    "highlight": "bold white on blue",
})

console = Console(theme=THEME)

# Helper functions
def success(msg: str):
    console.print(f"[success]✓[/success] {msg}")

def error(msg: str):
    console.print(f"[error]✗[/error] {msg}")

def warning(msg: str):
    console.print(f"[warning]⚠[/warning] {msg}")

def info(msg: str):
    console.print(f"[info]ℹ[/info] {msg}")
```

### Usage in Commands

```python
from mycli.utils.styles import console, success, error, warning

@app.command()
def deploy():
    """Deploy with consistent styling"""
    console.print("[primary]Starting deployment...[/primary]")

    try:
        # Deploy steps
        success("Build completed")
        success("Tests passed")
        warning("Skipped optional step")
        success("Deployment complete")
    except Exception as e:
        error(f"Deployment failed: {e}")
        raise typer.Exit(1)
```

### Custom Rich Renderables

```python
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.text import Text

def create_status_panel(title: str, status: str, color: str) -> Panel:
    """Create consistent status panels"""
    content = Text(status, style=color)
    return Panel(
        content,
        title=title,
        border_style=color,
        padding=(1, 2)
    )

@app.command()
def status():
    """Show status with custom renderables"""
    console.print(create_status_panel("Database", "Connected", "green"))
    console.print(create_status_panel("API", "Online", "green"))
    console.print(create_status_panel("Cache", "Warming up", "yellow"))
```

### Best Practices Summary

- ✅ Use type hints for all Typer parameters
- ✅ Provide help text for all commands and options
- ✅ Use Rich for all output (no plain print)
- ✅ Implement proper error handling with exit codes
- ✅ Create consistent styling/theme across commands
- ✅ Add `--version` flag
- ✅ Write tests using `CliRunner`
- ✅ Document with docstrings
- ✅ Use sub-commands for complex CLIs
- ✅ Keep business logic separate from CLI code
- ✅ Use Rich logging instead of print
- ✅ Handle keyboard interrupts gracefully
- ✅ Test on multiple platforms
