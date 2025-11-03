# Rich - Terminal Formatting Library

Rich is a Python library for rendering beautiful text and advanced formatting in the terminal. It provides an intuitive API for adding color, style, tables, progress bars, syntax highlighting, markdown rendering, and more to command-line applications. Rich works across Linux, macOS, and Windows, with support for true color, emoji, and automatic detection of terminal capabilities.

The library is built around the `Console` class, which handles all terminal output with intelligent width detection, text wrapping, and style management. Rich includes a comprehensive set of renderables (objects that can be displayed) including tables, trees, panels, progress bars, and syntax-highlighted code. All components are designed to work seamlessly together, allowing developers to build sophisticated terminal UIs with minimal code. The library integrates with Python's standard logging module and works in Jupyter notebooks without additional configuration.

## Console Print with Markup

Print styled text to the terminal using BBCode-like markup syntax for inline formatting.

```python
from rich.console import Console

console = Console()

# Basic printing with markup
console.print("Hello, [bold magenta]World[/bold magenta]!")
console.print("This is [bold]bold[/bold], [italic]italic[/italic], and [underline]underlined[/underline]")

# Combining styles and colors
console.print("[bold red on white]Error:[/] Something went wrong")
console.print("[link=https://example.com]Click here[/link]")

# Emoji support
console.print(":rocket: Launching application :tada:")

# Multiple objects with separator
console.print("Item 1", "Item 2", "Item 3", sep=" | ")

# Style entire output
console.print("Styled text", style="bold blue on yellow")
```

## Console Log with Timestamp

Log messages with automatic timestamps, file location, and pretty-printed data structures.

```python
from rich.console import Console

console = Console()

# Basic logging
console.log("Application started")
console.log("Processing user data", style="green")

# Log with data structures
data = {"user": "alice", "score": 95, "active": True}
console.log("User data:", data)

# Log with local variables visible
def process_payment(amount, currency):
    status = "pending"
    transaction_id = "TX-12345"
    console.log("Processing payment", log_locals=True)

process_payment(100.00, "USD")

# Expected output includes timestamp like:
# [12:34:56] Processing payment
#            amount = 100.0
#            currency = 'USD'
#            status = 'pending'
#            transaction_id = 'TX-12345'
```

## Rich Print Function

Drop-in replacement for Python's built-in print with automatic rich formatting.

```python
from rich import print

# Works like built-in print but with Rich features
print("Hello, [bold cyan]World[/]!")

# Pretty-print data structures
data = {
    "name": "Alice",
    "scores": [95, 87, 92],
    "metadata": {"active": True, "level": 5}
}
print(data)

# Print with separators and endings
print("Item 1", "Item 2", "Item 3", sep=" -> ", end="\n\n")

# Emoji rendering
print(":snake: Python :fire:")
```

## Inspect Objects

Generate detailed inspection reports for any Python object, showing attributes, methods, and documentation.

```python
from rich import inspect

# Inspect a list
my_list = [1, 2, 3]
inspect(my_list)

# Show methods
inspect(my_list, methods=True)

# Inspect custom objects with full help
class User:
    """Represents a user in the system."""

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def send_notification(self):
        """Send a notification to the user."""
        pass

user = User("Alice", "alice@example.com")
inspect(user, methods=True, help=True)

# Show private attributes
inspect(user, private=True, all=True)
```

## Table Creation

Create beautifully formatted tables with customizable columns, styling, and borders.

```python
from rich.console import Console
from rich.table import Table

console = Console()

# Create table with title and styling
table = Table(title="Star Wars Movies", show_header=True, header_style="bold magenta")

# Add columns with specific styles and alignment
table.add_column("Date", style="cyan", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Box Office", justify="right", style="green")

# Add rows
table.add_row("Dec 20, 2019", "The Rise of Skywalker", "$952,110,690")
table.add_row("May 25, 2018", "[red]Solo[/red]", "$393,151,347")
table.add_row("Dec 15, 2017", "The Last Jedi", "[bold]$1,332,539,889[/bold]")

console.print(table)

# Table with footer
sales_table = Table(show_footer=True)
sales_table.add_column("Product", footer="Total")
sales_table.add_column("Revenue", justify="right", footer="$25,000")
sales_table.add_row("Widget A", "$10,000")
sales_table.add_row("Widget B", "$15,000")
console.print(sales_table)
```

## Table Grid Layout

Create invisible tables for flexible layouts without visible borders.

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Grid with no borders for layout
grid = Table.grid(padding=1)
grid.add_column(style="cyan", justify="right")
grid.add_column(style="magenta")

grid.add_row("Name:", "Alice Johnson")
grid.add_row("Email:", "alice@example.com")
grid.add_row("Status:", "[green]Active[/green]")

console.print(Panel(grid, title="User Info"))

# Multi-column layout
layout = Table.grid(expand=True)
layout.add_column(ratio=1)
layout.add_column(ratio=2)
layout.add_row(
    Panel("Sidebar\nContent", style="blue"),
    Panel("Main\nContent\nArea", style="green")
)
console.print(layout)
```

## Progress Bars

Track progress of long-running operations with customizable progress displays.

```python
from rich.progress import Progress, track
import time

# Simple progress tracking
for item in track(range(100), description="Processing..."):
    time.sleep(0.01)

# Multiple progress bars with custom columns
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    TimeRemainingColumn(),
) as progress:
    download = progress.add_task("[cyan]Downloading...", total=1000)
    process = progress.add_task("[green]Processing...", total=1000)

    while not progress.finished:
        progress.update(download, advance=5)
        progress.update(process, advance=3)
        time.sleep(0.01)
```

## Download Progress

Display file download progress with transfer speeds and file sizes.

```python
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TextColumn,
)
import time

# Download-specific progress display
progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)

with progress:
    task_id = progress.add_task("download", filename="data.zip", total=10485760, start=False)
    progress.start_task(task_id)

    # Simulate download
    downloaded = 0
    while downloaded < 10485760:
        chunk = 32768
        downloaded += chunk
        progress.update(task_id, advance=chunk)
        time.sleep(0.01)
```

## Syntax Highlighting

Display syntax-highlighted code with line numbers and custom themes.

```python
from rich.console import Console
from rich.syntax import Syntax

console = Console()

# Highlight code string
code = '''
def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''

syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
console.print(syntax)

# Highlight from file
syntax = Syntax.from_path(
    "script.py",
    line_numbers=True,
    theme="monokai",
    code_width=88
)
console.print(syntax)

# Highlight specific lines
syntax = Syntax(
    code,
    "python",
    theme="dracula",
    line_numbers=True,
    highlight_lines={3, 4, 5},  # Highlight these line numbers
    start_line=1
)
console.print(syntax)
```

## Markdown Rendering

Render markdown documents with syntax highlighting for code blocks.

```python
from rich.console import Console
from rich.markdown import Markdown

console = Console()

MARKDOWN = """
# Project Overview

This is a **bold** statement and this is *italic*.

## Features

- Fast performance
- Easy to use
- Well documented

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

## Installation

```bash
pip install rich
```

> This is a blockquote with important information.

| Feature | Status |
| ------- | ------ |
| Tables  | ✓      |
| Code    | ✓      |
"""

markdown = Markdown(MARKDOWN, code_theme="monokai")
console.print(markdown)

# Load from file
with open("README.md") as f:
    markdown = Markdown(f.read())
console.print(markdown)
```

## Tree Display

Create hierarchical tree structures for displaying file systems or nested data.

```python
from rich.console import Console
from rich.tree import Tree

console = Console()

# Simple tree
tree = Tree("🌲 Project Root")
tree.add("📁 src").add("📄 main.py")
tree.add("📁 tests").add("📄 test_main.py")
tree.add("📄 README.md")
console.print(tree)

# Nested tree with styles
tree = Tree("[bold blue]Company", guide_style="bold cyan")

engineering = tree.add("[bold magenta]Engineering")
engineering.add("Alice (Backend)")
engineering.add("Bob (Frontend)")

sales = tree.add("[bold green]Sales")
sales.add("Carol (Enterprise)")
sales.add("David (SMB)")

console.print(tree)

# File system tree
import pathlib
from rich.filesize import decimal
from rich.markup import escape
from rich.text import Text

def build_tree(directory, tree):
    for path in sorted(pathlib.Path(directory).iterdir()):
        if path.is_dir():
            branch = tree.add(f"📁 {escape(path.name)}", style="bold magenta")
            build_tree(path, branch)
        else:
            size = decimal(path.stat().st_size)
            tree.add(f"📄 {escape(path.name)} ({size})")

tree = Tree(f"📂 /home/user/project")
build_tree("/home/user/project", tree)
console.print(tree)
```

## Panel Borders

Wrap content in decorative panels with titles, borders, and padding.

```python
from rich.console import Console
from rich.panel import Panel

console = Console()

# Simple panel
console.print(Panel("Hello, World!"))

# Panel with title and styling
console.print(
    Panel(
        "This is the content of the panel",
        title="Welcome",
        border_style="blue"
    )
)

# Panel with subtitle and padding
console.print(
    Panel(
        "[bold cyan]Success![/]\n\nThe operation completed successfully.",
        title="✓ Status",
        subtitle="Press any key to continue",
        padding=(1, 2),
        border_style="green"
    )
)

# Fit panel to content
console.print(Panel.fit("Compact panel", border_style="red"))

# Panel with custom box style
from rich import box
console.print(
    Panel(
        "Double border style",
        box=box.DOUBLE,
        title="Important"
    )
)
```

## Layout Splitting

Divide terminal space into resizable regions for complex layouts.

```python
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel

console = Console()

# Create layout
layout = Layout()

# Split into header, main, footer
layout.split_column(
    Layout(name="header", size=3),
    Layout(name="main"),
    Layout(name="footer", size=3)
)

# Split main into sidebar and content
layout["main"].split_row(
    Layout(name="sidebar", ratio=1),
    Layout(name="content", ratio=3)
)

# Update regions
layout["header"].update(Panel("🎯 Application Header", style="bold white on blue"))
layout["sidebar"].update(Panel("Navigation\n- Home\n- Settings\n- Help"))
layout["content"].update(Panel("Main content area\n\nLorem ipsum..."))
layout["footer"].update(Panel("Status: Ready", style="white on dark_green"))

console.print(layout)

# Dynamic layout updates
from rich.live import Live
import time

layout = Layout()
layout.split_row(
    Layout(name="left"),
    Layout(name="right")
)

with Live(layout, refresh_per_second=4):
    for i in range(10):
        layout["left"].update(Panel(f"Counter: {i}"))
        layout["right"].update(Panel(f"Countdown: {10-i}"))
        time.sleep(0.5)
```

## Live Rendering

Auto-refresh displays for dynamic content updates.

```python
from rich.console import Console
from rich.live import Live
from rich.table import Table
import time

console = Console()

# Live updating table
table = Table()
table.add_column("Status")
table.add_column("Progress")

with Live(table, refresh_per_second=4):
    for i in range(20):
        table.add_row(f"Task {i}", f"{i*5}%")
        time.sleep(0.2)

# Live panel updates
from rich.panel import Panel

with Live(console=console, refresh_per_second=10) as live:
    for i in range(100):
        live.update(
            Panel(
                f"[bold cyan]Processing: {i}%[/]\n"
                f"{'█' * (i // 2)}{' ' * (50 - i // 2)}",
                title="Progress"
            )
        )
        time.sleep(0.05)

# Live with alternate screen
with Live(Panel("Full screen mode"), screen=True, refresh_per_second=4) as live:
    for i in range(10):
        live.update(Panel(f"Frame {i}"))
        time.sleep(0.5)
```

## Status Spinner

Display animated spinner for indeterminate operations.

```python
from rich.console import Console
import time

console = Console()

# Simple status
with console.status("[bold green]Processing...") as status:
    time.sleep(2)
    status.update("[bold blue]Still working...")
    time.sleep(2)

# Status with logging
with console.status("[bold green]Working on tasks...") as status:
    tasks = ["task1", "task2", "task3"]
    for task in tasks:
        console.log(f"Starting {task}")
        time.sleep(1)
        console.log(f"[green]Completed {task}[/]")

# Custom spinner
with console.status("Loading...", spinner="dots12"):
    time.sleep(3)

# Available spinners: dots, line, simpleDotsScrolling, aesthetic, etc.
# Run: python -m rich.spinner to see all options
```

## Logging Handler

Integrate Rich formatting with Python's logging module.

```python
import logging
from rich.logging import RichHandler

# Configure logging with Rich handler
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=True)]
)

log = logging.getLogger("rich")

# Use standard logging
log.info("Application started")
log.warning("Low disk space detected")
log.error("Failed to connect to database")

# With rich tracebacks
try:
    result = 10 / 0
except Exception:
    log.exception("Error occurred")

# Custom configuration
handler = RichHandler(
    show_time=True,
    show_level=True,
    show_path=True,
    markup=True,
    rich_tracebacks=True,
    tracebacks_show_locals=True,
    tracebacks_extra_lines=5
)

logger = logging.getLogger("app")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger.debug("Debug information")
logger.info("[bold blue]Processing user data[/]")
logger.error("[bold red]Critical error[/]")
```

## Pretty Print

Automatically format Python objects with syntax highlighting.

```python
from rich import pretty
from rich.console import Console

# Install in REPL for automatic pretty printing
pretty.install()

# Now all output is automatically formatted
data = {
    "name": "Alice",
    "age": 30,
    "skills": ["Python", "JavaScript", "SQL"],
    "metadata": {
        "active": True,
        "score": 95.5,
        "badges": ["gold", "platinum"]
    }
}

print(data)  # Automatically pretty-printed

# Pretty print with console
console = Console()

class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return f"User({self.name!r}, {self.email!r})"

user = User("Bob", "bob@example.com")
console.print(user)

# Pretty print with custom depth
complex_data = {"level1": {"level2": {"level3": {"level4": "deep"}}}}
from rich.pretty import pprint
pprint(complex_data, max_depth=2)
```

## JSON Printing

Format and syntax highlight JSON data.

```python
from rich import print_json
from rich.console import Console

console = Console()

# Print JSON string
json_str = '{"name": "Alice", "age": 30, "active": true}'
print_json(json_str)

# Print Python data as JSON
data = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ],
    "total": 2,
    "success": True
}

print_json(data=data)

# Console method
console.print_json(data=data, indent=2)

# From file
import json
with open("data.json") as f:
    json_data = f.read()
print_json(json_data)

# Sort keys
print_json(data={"z": 1, "a": 2, "m": 3}, sort_keys=True)
```

## Console Rule

Draw horizontal dividers with optional titles.

```python
from rich.console import Console

console = Console()

# Simple rule
console.rule()

# Rule with title
console.rule("[bold red]Section 1")
console.print("Content here...")
console.rule("[bold blue]Section 2")
console.print("More content...")

# Rule with alignment
console.rule("[bold green]Left Aligned", align="left")
console.rule("[bold yellow]Right Aligned", align="right")
console.rule("[bold magenta]Center Aligned", align="center")

# Custom characters
console.rule("Custom", characters="=")
console.rule("Dots", characters=".")
console.rule("Stars", characters="*")
```

## Traceback Formatting

Display beautiful, informative exception tracebacks.

```python
from rich.console import Console
from rich.traceback import install

# Install as default traceback handler
install(show_locals=True)

# Now all exceptions are beautifully formatted
def divide(a, b):
    return a / b

def calculate(x, y):
    result = divide(x, y)
    return result

try:
    calculate(10, 0)
except Exception:
    console = Console()
    console.print_exception(show_locals=True)

# Custom traceback
from rich.traceback import Traceback

try:
    1 / 0
except Exception:
    console.print(Traceback(
        width=100,
        extra_lines=3,
        theme="monokai",
        word_wrap=True,
        show_locals=True
    ))
```

## Rich is designed for building professional command-line interfaces with minimal effort. The library excels at data visualization, progress tracking, and debugging with its rich output capabilities. Common use cases include CLI tools, system administration scripts, data processing pipelines, and development utilities. The Console class serves as the central hub, providing intelligent terminal handling and output formatting.

Integration patterns typically involve creating a single Console instance for an application and using it throughout the codebase. Rich works seamlessly with existing Python code through the drop-in `rich.print()` replacement and logging handler integration. For long-running tasks, combine Progress bars with Live rendering for real-time updates. Complex layouts benefit from Layout splitting combined with panels and tables. The library's automatic terminal capability detection ensures output degrades gracefully across different environments, from modern terminals with true color support to legacy systems with limited capabilities.
