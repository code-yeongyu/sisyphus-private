# Troubleshooting Guide

Common issues and solutions when building CLIs with Typer and Rich.

## Table of Contents

1. [Display Issues](#display-issues)
2. [Typer Parameter Issues](#typer-parameter-issues)
3. [Rich Rendering Issues](#rich-rendering-issues)
4. [Testing Issues](#testing-issues)
5. [Packaging Issues](#packaging-issues)
6. [Performance Issues](#performance-issues)

---

## Display Issues

### Colors Not Showing on Windows

**Problem:** ANSI colors and Rich formatting don't display on Windows.

**Solution:**
```python
import os
os.system("")  # Enable ANSI on Windows

from rich.console import Console
console = Console()
```

Or use Rich's force_terminal:
```python
console = Console(force_terminal=True)
```

### Unicode Characters Not Displaying

**Problem:** Box drawing characters or emojis show as `?` or garbled text.

**Solutions:**

1. Check terminal encoding:
```python
import sys
print(sys.stdout.encoding)  # Should be 'utf-8'
```

2. Set encoding explicitly:
```python
from rich.console import Console
console = Console(force_terminal=True, legacy_windows=False)
```

3. Use ASCII-safe alternatives:
```python
from rich.console import Console
console = Console(legacy_windows=True)  # Use ASCII characters
```

### Progress Bar Not Updating

**Problem:** Progress bar appears frozen or doesn't update smoothly.

**Solution:** Ensure you're calling `update()` or `advance()`:
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("Processing...", total=100)

    for i in range(100):
        # Do work
        progress.update(task, advance=1)  # ← Must call this
        # or: progress.advance(task)
```

### Output Appears After Program Exits

**Problem:** Rich output only shows after the program finishes.

**Solution:** Flush the console or use `console.print()` instead of `print()`:
```python
console = Console()
console.print("Hello")  # Immediate output

# Or if using print():
print("Hello", flush=True)
```

---

## Typer Parameter Issues

### Required Option Not Enforcing

**Problem:** Typer option with `...` default still allows empty value.

**Solution:** Use the correct syntax:
```python
# ✗ Wrong
@app.command()
def cmd(api_key: str = typer.Option(...)):
    pass

# ✓ Correct
@app.command()
def cmd(api_key: str = typer.Option(..., help="API key (required)")):
    pass

# Or use Argument for truly required:
@app.command()
def cmd(api_key: str = typer.Argument(..., help="API key")):
    pass
```

### Boolean Flag Not Working

**Problem:** `--verbose` doesn't toggle the boolean.

**Solution:** Use correct boolean flag pattern:
```python
# ✓ Correct - This creates --verbose and --no-verbose
@app.command()
def cmd(verbose: bool = typer.Option(False, help="Enable verbose")):
    pass

# ✓ Also correct - Custom flag names
@app.command()
def cmd(verbose: bool = typer.Option(False, "--verbose", "-v")):
    pass
```

### List Options Not Accepting Multiple Values

**Problem:** Can't pass multiple values to a list option.

**Solution:**
```python
from typing import List, Optional

# ✓ Correct
@app.command()
def cmd(tags: Optional[List[str]] = typer.Option(None)):
    pass

# Usage:
# mycli cmd --tags tag1 --tags tag2 --tags tag3
```

### Path Validation Not Working

**Problem:** File/directory validation doesn't trigger.

**Solution:** Use correct Path parameters:
```python
from pathlib import Path

@app.command()
def cmd(
    input_file: Path = typer.Option(
        ...,
        exists=True,        # Must exist
        file_okay=True,     # Accept files
        dir_okay=False,     # Reject directories
        readable=True,      # Must be readable
        resolve_path=True,  # Resolve to absolute path
    )
):
    pass
```

### Callback Not Executing

**Problem:** Version callback doesn't run.

**Solution:** Use `is_eager=True`:
```python
def version_callback(value: bool):
    if value:
        console.print("Version 1.0.0")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,  # ← Required for callbacks
    )
):
    pass
```

---

## Rich Rendering Issues

### Table Not Displaying Properly

**Problem:** Table columns misaligned or text wrapping incorrectly.

**Solutions:**

1. Set explicit column widths:
```python
table.add_column("Name", width=20)
table.add_column("Description", width=50)
```

2. Disable wrapping:
```python
table.add_column("ID", no_wrap=True)
```

3. Set column style:
```python
table.add_column("Status", justify="center", style="bold")
```

### Panel Border Characters Broken

**Problem:** Panel borders show garbled characters.

**Solution:** Use ASCII box or change box style:
```python
from rich.panel import Panel
from rich import box

# Use ASCII
panel = Panel("Content", box=box.ASCII)

# Or different style
panel = Panel("Content", box=box.ROUNDED)
```

### Syntax Highlighting Not Working

**Problem:** Code blocks display without syntax highlighting.

**Solutions:**

1. Install Pygments:
```bash
pip install pygments
```

2. Specify language explicitly:
```python
from rich.syntax import Syntax

syntax = Syntax(
    code,
    "python",  # ← Explicit language
    theme="monokai",
    line_numbers=True
)
console.print(syntax)
```

### Rich Output in Logs Appears Garbled

**Problem:** Rich formatting breaks when redirecting to files.

**Solution:** Detect if output is a TTY:
```python
from rich.console import Console
import sys

console = Console(file=sys.stdout, force_terminal=sys.stdout.isatty())

# Or disable Rich when not in terminal:
if sys.stdout.isatty():
    console = Console()
else:
    console = Console(no_color=True, force_terminal=False)
```

---

## Testing Issues

### Typer Tests Not Capturing Rich Output

**Problem:** `CliRunner` doesn't capture Rich formatted output.

**Solution:** Use Rich's capture:
```python
from typer.testing import CliRunner
from rich.console import Console

runner = CliRunner(mix_stderr=False)

def test_command():
    # Test with CliRunner (captures plain text)
    result = runner.invoke(app, ["command"])
    assert "output" in result.stdout

    # Or test Rich directly with capture
    console = Console()
    with console.capture() as capture:
        console.print("[bold]Test[/bold]")
    output = capture.get()
    assert "Test" in output
```

### Tests Fail in CI But Pass Locally

**Problem:** Rich rendering behaves differently in CI environments.

**Solution:** Mock or disable Rich in tests:
```python
# conftest.py
import pytest
from rich.console import Console

@pytest.fixture
def console():
    """Provide console for testing"""
    return Console(force_terminal=True, width=80)

# Or disable Rich in CI:
import os
if os.getenv("CI"):
    console = Console(no_color=True, force_terminal=False)
```

### Interactive Prompts Block Tests

**Problem:** Tests hang on `Prompt.ask()` or `Confirm.ask()`.

**Solution:** Use input parameter in CliRunner:
```python
def test_interactive():
    result = runner.invoke(
        app,
        ["configure"],
        input="John\n30\ny\n"  # Provide inputs
    )
    assert result.exit_code == 0
```

### Mock Not Working with Typer Commands

**Problem:** Mocked functions not being called in Typer commands.

**Solution:** Patch at the right location:
```python
from unittest.mock import patch

# ✗ Wrong - patching definition location
@patch('mymodule.api_call')
def test_command(mock_api):
    ...

# ✓ Correct - patch where it's used
@patch('myapp.commands.api_call')
def test_command(mock_api):
    ...
```

---

## Packaging Issues

### Entry Point Not Working After Install

**Problem:** `mycli` command not found after `pip install`.

**Solution:** Check pyproject.toml entry point:
```toml
[project.scripts]
mycli = "mycli.cli:app"  # Format: package.module:callable
```

Ensure your `cli.py` has:
```python
app = typer.Typer()

if __name__ == "__main__":
    app()
```

### Import Errors After Installation

**Problem:** `ModuleNotFoundError` when running installed CLI.

**Solutions:**

1. Check package structure:
```
mycli/
├── __init__.py  # ← Must exist
├── cli.py
└── commands/
    └── __init__.py  # ← Must exist
```

2. Verify pyproject.toml packages:
```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["mycli*"]
```

### Dependencies Not Installing

**Problem:** Required packages missing after install.

**Solution:** Check dependencies in pyproject.toml:
```toml
[project]
dependencies = [
    "typer[all]>=0.9.0",  # [all] includes shell completion
    "rich>=13.0.0",
]
```

### CLI Slow to Start

**Problem:** Command takes several seconds to become responsive.

**Solutions:**

1. Use lazy imports:
```python
@app.command()
def heavy_command():
    # Import only when needed
    import pandas
    import numpy
    # ...
```

2. Profile startup:
```bash
python -X importtime -m mycli 2> import_time.log
```

3. Reduce dependencies in main module.

---

## Performance Issues

### Progress Bar Slowing Down Operations

**Problem:** Operations slower with progress bar enabled.

**Solution:** Update less frequently:
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("Processing...", total=1000)

    for i in range(1000):
        # Do work
        if i % 10 == 0:  # Update every 10 items
            progress.update(task, completed=i)

    progress.update(task, completed=1000)  # Final update
```

### Rich Logging Creates Large Log Files

**Problem:** Log files grow too large with Rich formatting.

**Solution:** Disable Rich for file logging:
```python
import logging
from rich.logging import RichHandler

# Console handler with Rich
console_handler = RichHandler()

# File handler without Rich
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))

logging.basicConfig(
    level="INFO",
    handlers=[console_handler, file_handler]
)
```

### Live Display Causes High CPU

**Problem:** `Live()` context uses too much CPU.

**Solution:** Reduce refresh rate:
```python
from rich.live import Live

with Live(generate_table(), refresh_per_second=2) as live:  # Default is 4
    for i in range(100):
        time.sleep(1)
        live.update(generate_table())
```

### Memory Leak with Long-Running CLI

**Problem:** Memory usage grows over time.

**Solutions:**

1. Reuse console instance:
```python
# At module level
console = Console()

# Use throughout
@app.command()
def cmd():
    console.print("Hello")
```

2. Clear console history:
```python
console.clear()  # Clear screen
```

3. Use context managers properly:
```python
# ✓ Correct - cleans up automatically
with Progress() as progress:
    # ...

# ✗ Wrong - might leak
progress = Progress()
progress.start()
# ... (might forget to stop)
```

---

## Platform-Specific Issues

### macOS: Command Not Found After Install

**Problem:** `mycli` not in PATH on macOS.

**Solution:** Add Python scripts to PATH:
```bash
# Add to ~/.zshrc or ~/.bash_profile
export PATH="$HOME/Library/Python/3.x/bin:$PATH"

# Or use pipx (recommended)
pipx install mycli
```

### Windows: Script Extension Not Recognized

**Problem:** Must type `mycli.exe` instead of `mycli` on Windows.

**Solution:** Ensure `.exe` wrapper is created:
```toml
[project.scripts]
mycli = "mycli.cli:app"  # setuptools creates .exe automatically
```

Or add `.PY` to PATHEXT environment variable.

### Linux: Permission Denied

**Problem:** `./mycli` gives permission denied.

**Solution:**
```bash
chmod +x mycli

# Or install properly:
pip install -e .
```

---

## Debug Techniques

### Enable Typer Debug Mode

```python
app = typer.Typer()

@app.callback()
def main(
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode")
):
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
```

### Inspect Rich Renderables

```python
from rich import inspect

# Inspect any Rich object
inspect(my_table, methods=True)
```

### Capture and Print Output

```python
from rich.console import Console

console = Console()

with console.capture() as capture:
    console.print("[bold]Test[/bold]")

output = capture.get()
print(repr(output))  # See raw output with escape codes
```

### Profile CLI Performance

```bash
# Time imports
python -X importtime -m mycli 2> import_time.log

# Profile execution
python -m cProfile -o profile.stats -m mycli command

# View profile
python -m pstats profile.stats
```

---

## Getting Help

### Resources

- **Typer Documentation**: https://typer.tiangolo.com/
- **Rich Documentation**: https://rich.readthedocs.io/
- **Typer GitHub Issues**: https://github.com/tiangolo/typer/issues
- **Rich GitHub Issues**: https://github.com/Textualize/rich/issues

### Reporting Bugs

When reporting issues, include:

1. Python version: `python --version`
2. Typer version: `pip show typer`
3. Rich version: `pip show rich`
4. Terminal type: `echo $TERM` (Unix) or check Windows Terminal version
5. Minimal reproducible example
6. Expected vs actual behavior
7. Error messages and tracebacks

### Community

- **Typer Discussions**: https://github.com/tiangolo/typer/discussions
- **Rich Discussions**: https://github.com/Textualize/rich/discussions
- **Python Discord**: Rich channel in Python Discord server
