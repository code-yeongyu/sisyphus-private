# Real-World Examples

Complete, production-ready CLI applications demonstrating best practices.

## Table of Contents

1. [Database Migration Tool](#1-database-migration-tool)
2. [File Processing CLI](#2-file-processing-cli)
3. [API Client](#3-api-client)
4. [Build Tool](#4-build-tool)
5. [System Monitor](#5-system-monitor)
6. [Code Generator](#6-code-generator)

---

## 1. Database Migration Tool

Complete database migration CLI with rollback support.

```python
#!/usr/bin/env python3
"""Database migration tool - dbmigrate"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

app = typer.Typer(help="Database migration tool")
console = Console()

MIGRATIONS_DIR = Path("migrations")
STATE_FILE = Path(".migrations.json")

def load_state() -> dict:
    """Load migration state"""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"applied": []}

def save_state(state: dict):
    """Save migration state"""
    STATE_FILE.write_text(json.dumps(state, indent=2))

@app.command()
def init():
    """Initialize migrations directory"""
    MIGRATIONS_DIR.mkdir(exist_ok=True)

    template = '''"""Migration: {name}"""

def up():
    """Apply migration"""
    # Add your migration code here
    pass

def down():
    """Rollback migration"""
    # Add your rollback code here
    pass
'''

    example_file = MIGRATIONS_DIR / "001_example.py"
    example_file.write_text(template.format(name="Example migration"))

    console.print(Panel(
        f"[green]✓[/green] Migrations directory created at [cyan]{MIGRATIONS_DIR}[/cyan]\n"
        f"[green]✓[/green] Example migration created",
        title="Initialization Complete",
        border_style="green"
    ))

@app.command()
def create(name: str):
    """Create new migration file"""
    # Get next migration number
    existing = sorted(MIGRATIONS_DIR.glob("*.py"))
    next_num = len(existing) + 1

    filename = f"{next_num:03d}_{name}.py"
    filepath = MIGRATIONS_DIR / filename

    template = f'''"""Migration: {name}"""
from datetime import datetime

def up():
    """Apply migration"""
    print(f"Applying migration: {name}")
    # Add your migration code here

def down():
    """Rollback migration"""
    print(f"Rolling back migration: {name}")
    # Add your rollback code here
'''

    filepath.write_text(template)
    console.print(f"[green]✓[/green] Created migration: [cyan]{filename}[/cyan]")

@app.command()
def status():
    """Show migration status"""
    state = load_state()
    applied = set(state.get("applied", []))

    migrations = sorted(MIGRATIONS_DIR.glob("*.py"))

    table = Table(title="Migration Status", show_header=True)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Name", style="white")
    table.add_column("Status", style="magenta", justify="center")
    table.add_column("Applied At", style="dim")

    for migration in migrations:
        name = migration.stem
        status_text = "[green]✓ Applied[/green]" if name in applied else "[yellow]⏸ Pending[/yellow]"
        applied_at = state.get("applied_at", {}).get(name, "")

        parts = name.split("_", 1)
        num = parts[0] if len(parts) > 1 else ""
        migration_name = parts[1] if len(parts) > 1 else name

        table.add_row(num, migration_name, status_text, applied_at)

    console.print(table)
    console.print(f"\n[dim]Total: {len(migrations)} migrations, {len(applied)} applied[/dim]")

@app.command()
def up(
    steps: Optional[int] = typer.Option(None, help="Number of migrations to apply"),
    all: bool = typer.Option(False, "--all", help="Apply all pending migrations")
):
    """Apply pending migrations"""
    state = load_state()
    applied = set(state.get("applied", []))
    applied_at = state.get("applied_at", {})

    migrations = sorted(MIGRATIONS_DIR.glob("*.py"))
    pending = [m for m in migrations if m.stem not in applied]

    if not pending:
        console.print("[yellow]No pending migrations[/yellow]")
        return

    to_apply = pending if all else pending[:steps] if steps else pending[:1]

    console.print(f"[cyan]Applying {len(to_apply)} migration(s)...[/cyan]\n")

    for migration in track(to_apply, description="Migrating"):
        name = migration.stem

        try:
            # Execute migration
            exec_globals = {}
            exec(migration.read_text(), exec_globals)
            exec_globals["up"]()

            # Update state
            applied.add(name)
            applied_at[name] = datetime.now().isoformat()

            console.log(f"[green]✓[/green] Applied: {name}")

        except Exception as e:
            console.print(Panel(
                f"[red]Migration failed: {name}[/red]\n\n{str(e)}",
                title="❌ Error",
                border_style="red"
            ))
            raise typer.Exit(1)

    state["applied"] = list(applied)
    state["applied_at"] = applied_at
    save_state(state)

    console.print(f"\n[bold green]✓ Successfully applied {len(to_apply)} migration(s)[/bold green]")

@app.command()
def down(
    steps: int = typer.Option(1, help="Number of migrations to rollback")
):
    """Rollback migrations"""
    state = load_state()
    applied = state.get("applied", [])

    if not applied:
        console.print("[yellow]No migrations to rollback[/yellow]")
        return

    # Get migrations to rollback (last N applied)
    to_rollback = sorted(applied)[-steps:]

    console.print(f"[yellow]Rolling back {len(to_rollback)} migration(s)...[/yellow]\n")

    for name in track(reversed(to_rollback), description="Rolling back"):
        migration_file = MIGRATIONS_DIR / f"{name}.py"

        if not migration_file.exists():
            console.print(f"[red]✗[/red] Migration file not found: {name}")
            continue

        try:
            # Execute rollback
            exec_globals = {}
            exec(migration_file.read_text(), exec_globals)
            exec_globals["down"]()

            # Update state
            applied.remove(name)
            state.get("applied_at", {}).pop(name, None)

            console.log(f"[green]✓[/green] Rolled back: {name}")

        except Exception as e:
            console.print(Panel(
                f"[red]Rollback failed: {name}[/red]\n\n{str(e)}",
                title="❌ Error",
                border_style="red"
            ))
            raise typer.Exit(1)

    state["applied"] = applied
    save_state(state)

    console.print(f"\n[bold green]✓ Successfully rolled back {len(to_rollback)} migration(s)[/bold green]")

if __name__ == "__main__":
    app()
```

**Usage:**
```bash
# Initialize
python dbmigrate.py init

# Create migration
python dbmigrate.py create "add_users_table"

# Check status
python dbmigrate.py status

# Apply migrations
python dbmigrate.py up --all

# Rollback
python dbmigrate.py down --steps 2
```

---

## 2. File Processing CLI

Batch file processor with progress tracking and error recovery.

```python
#!/usr/bin/env python3
"""File processing CLI - fileproc"""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from typing import List, Optional
import shutil
from datetime import datetime

app = typer.Typer(help="File processing tool")
console = Console()

@app.command()
def convert(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Input directory"),
    output_dir: Path = typer.Argument(..., help="Output directory"),
    pattern: str = typer.Option("*.txt", help="File pattern to match"),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Process recursively"),
    overwrite: bool = typer.Option(False, help="Overwrite existing files"),
    dry_run: bool = typer.Option(False, help="Show what would be done without doing it")
):
    """Convert files with progress tracking"""

    # Find files
    if recursive:
        files = list(input_dir.rglob(pattern))
    else:
        files = list(input_dir.glob(pattern))

    if not files:
        console.print(f"[yellow]No files matching pattern '{pattern}' found[/yellow]")
        return

    console.print(f"[cyan]Found {len(files)} file(s) to process[/cyan]\n")

    # Show preview
    if dry_run:
        table = Table(title="Dry Run - Files to Process")
        table.add_column("Source", style="cyan")
        table.add_column("Destination", style="green")

        for file in files[:10]:  # Show first 10
            rel_path = file.relative_to(input_dir)
            dest = output_dir / rel_path
            table.add_row(str(file), str(dest))

        if len(files) > 10:
            table.add_row("...", f"... and {len(files) - 10} more")

        console.print(table)
        return

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process files
    errors = []
    success_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
    ) as progress:

        task = progress.add_task("[cyan]Processing files...", total=len(files))

        for file in files:
            try:
                # Calculate destination
                rel_path = file.relative_to(input_dir)
                dest = output_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)

                # Check if exists
                if dest.exists() and not overwrite:
                    errors.append((file, "File exists (use --overwrite)"))
                    progress.update(task, advance=1)
                    continue

                # Process file (example: copy and uppercase)
                content = file.read_text()
                dest.write_text(content.upper())

                success_count += 1

            except Exception as e:
                errors.append((file, str(e)))

            progress.update(task, advance=1)

    # Report
    console.print(f"\n[bold green]✓ Successfully processed: {success_count}/{len(files)}[/bold green]")

    if errors:
        console.print(f"\n[bold red]✗ Errors: {len(errors)}[/bold red]")

        error_table = Table(title="Errors")
        error_table.add_column("File", style="cyan")
        error_table.add_column("Error", style="red")

        for file, error in errors[:20]:  # Show first 20 errors
            error_table.add_row(str(file), error)

        if len(errors) > 20:
            error_table.add_row("...", f"... and {len(errors) - 20} more errors")

        console.print(error_table)

@app.command()
def stats(
    directory: Path = typer.Argument(..., exists=True, file_okay=False),
    pattern: str = typer.Option("*", help="File pattern"),
):
    """Show directory statistics"""

    files = list(directory.rglob(pattern))

    # Calculate stats
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    file_types = {}

    for file in files:
        if file.is_file():
            ext = file.suffix or "(no extension)"
            file_types[ext] = file_types.get(ext, 0) + 1

    # Display
    table = Table(title=f"Statistics for {directory}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Total Files", str(len(files)))
    table.add_row("Total Size", f"{total_size / 1024 / 1024:.2f} MB")
    table.add_row("File Types", str(len(file_types)))

    console.print(table)

    # File types breakdown
    types_table = Table(title="File Types")
    types_table.add_column("Extension", style="cyan")
    types_table.add_column("Count", style="magenta", justify="right")

    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
        types_table.add_row(ext, str(count))

    console.print(types_table)

if __name__ == "__main__":
    app()
```

---

## 3. API Client

REST API client with authentication and caching.

```python
#!/usr/bin/env python3
"""API Client - apicli"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt
from typing import Optional
import json
from pathlib import Path
import hashlib
import time

app = typer.Typer(help="API Client")
console = Console()

CONFIG_FILE = Path.home() / ".apicli" / "config.json"
CACHE_DIR = Path.home() / ".apicli" / "cache"

def load_config() -> dict:
    """Load configuration"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(config: dict):
    """Save configuration"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def get_cache_key(url: str) -> str:
    """Generate cache key from URL"""
    return hashlib.md5(url.encode()).hexdigest()

def get_cached(url: str, max_age: int = 3600) -> Optional[dict]:
    """Get cached response"""
    cache_file = CACHE_DIR / get_cache_key(url)

    if cache_file.exists():
        cache_time = cache_file.stat().st_mtime
        if time.time() - cache_time < max_age:
            return json.loads(cache_file.read_text())
    return None

def save_cache(url: str, data: dict):
    """Save to cache"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / get_cache_key(url)
    cache_file.write_text(json.dumps(data, indent=2))

@app.command()
def config(
    api_key: Optional[str] = typer.Option(None, help="API key"),
    base_url: Optional[str] = typer.Option(None, help="Base URL"),
):
    """Configure API client"""
    cfg = load_config()

    if api_key:
        cfg["api_key"] = api_key
        console.print("[green]✓[/green] API key saved")

    if base_url:
        cfg["base_url"] = base_url
        console.print("[green]✓[/green] Base URL saved")

    if not api_key and not base_url:
        # Interactive configuration
        cfg["api_key"] = Prompt.ask("Enter API key", default=cfg.get("api_key", ""))
        cfg["base_url"] = Prompt.ask("Enter base URL", default=cfg.get("base_url", "https://api.example.com"))

    save_config(cfg)
    console.print("\n[bold green]✓ Configuration saved[/bold green]")

@app.command()
def get(
    endpoint: str,
    no_cache: bool = typer.Option(False, help="Skip cache"),
    raw: bool = typer.Option(False, help="Show raw JSON"),
):
    """GET request to endpoint"""
    cfg = load_config()

    if "base_url" not in cfg:
        console.print("[red]✗ Not configured. Run 'apicli config' first[/red]")
        raise typer.Exit(1)

    url = f"{cfg['base_url']}/{endpoint.lstrip('/')}"

    # Check cache
    if not no_cache:
        cached = get_cached(url)
        if cached:
            console.print("[dim]Using cached response[/dim]\n")
            display_response(cached, raw)
            return

    # Make request (simulated)
    console.print(f"[cyan]GET {url}[/cyan]")

    # Simulate API call
    response = {
        "status": "success",
        "data": {
            "id": 1,
            "name": "Example",
            "created_at": "2025-10-18T00:00:00Z"
        }
    }

    # Save to cache
    save_cache(url, response)

    display_response(response, raw)

def display_response(data: dict, raw: bool = False):
    """Display API response"""
    if raw:
        syntax = Syntax(
            json.dumps(data, indent=2),
            "json",
            theme="monokai",
            line_numbers=True
        )
        console.print(syntax)
    else:
        # Pretty display
        if "data" in data and isinstance(data["data"], dict):
            table = Table(title="Response", show_header=True)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            for key, value in data["data"].items():
                table.add_row(key, str(value))

            console.print(table)
        else:
            console.print(Panel(json.dumps(data, indent=2)))

@app.command()
def clear_cache():
    """Clear response cache"""
    if CACHE_DIR.exists():
        import shutil
        shutil.rmtree(CACHE_DIR)
        console.print("[green]✓[/green] Cache cleared")
    else:
        console.print("[yellow]Cache is already empty[/yellow]")

if __name__ == "__main__":
    app()
```

---

## 4. Build Tool

Project build tool with dependency management.

```python
#!/usr/bin/env python3
"""Build Tool - build"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.tree import Tree
from pathlib import Path
import subprocess
import time
from typing import List

app = typer.Typer(help="Project build tool")
console = Console()

@app.command()
def clean():
    """Clean build artifacts"""
    artifacts = [
        "dist/",
        "build/",
        "*.egg-info",
        "__pycache__",
        "*.pyc",
        ".pytest_cache",
    ]

    with console.status("[yellow]Cleaning...", spinner="dots") as status:
        removed = []

        for pattern in artifacts:
            for path in Path(".").rglob(pattern):
                try:
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    removed.append(str(path))
                except Exception as e:
                    console.log(f"[red]Failed to remove {path}: {e}[/red]")

        time.sleep(0.5)  # Visual feedback

    console.print(f"\n[green]✓[/green] Removed {len(removed)} item(s)")

@app.command()
def test(
    coverage: bool = typer.Option(False, help="Run with coverage"),
    verbose: bool = typer.Option(False, "-v", help="Verbose output"),
):
    """Run tests"""
    cmd = ["pytest"]

    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])

    if verbose:
        cmd.append("-v")

    console.print(f"[cyan]Running: {' '.join(cmd)}[/cyan]\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        console.print("\n[bold green]✓ All tests passed[/bold green]")
    else:
        console.print("\n[bold red]✗ Tests failed[/bold red]")
        raise typer.Exit(1)

@app.command()
def lint():
    """Run linters"""
    linters = [
        ("black --check .", "Black (formatter check)"),
        ("ruff check .", "Ruff (linter)"),
        ("mypy .", "MyPy (type checker)"),
    ]

    results = {}

    for cmd, name in linters:
        console.print(f"\n[cyan]Running {name}...[/cyan]")

        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True
        )

        results[name] = result.returncode == 0

        if result.returncode == 0:
            console.print(f"[green]✓[/green] {name} passed")
        else:
            console.print(f"[red]✗[/red] {name} failed")
            if result.stdout:
                console.print(result.stdout)

    # Summary
    console.print("\n" + "=" * 50)
    passed = sum(1 for r in results.values() if r)
    total = len(results)

    if passed == total:
        console.print(f"[bold green]✓ All checks passed ({passed}/{total})[/bold green]")
    else:
        console.print(f"[bold red]✗ Some checks failed ({passed}/{total})[/bold red]")
        raise typer.Exit(1)

@app.command()
def build(
    dist_format: str = typer.Option("wheel", help="Distribution format (wheel/sdist)"),
):
    """Build distribution"""
    with console.status("[cyan]Building distribution...", spinner="dots") as status:
        # Run build
        result = subprocess.run(
            ["python", "-m", "build"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            console.print(Panel(
                f"[red]Build failed:[/red]\n\n{result.stderr}",
                title="❌ Error",
                border_style="red"
            ))
            raise typer.Exit(1)

    # Show build output
    dist_files = list(Path("dist").glob("*"))

    tree = Tree("📦 [bold cyan]Build Output[/bold cyan]")
    for file in dist_files:
        size = file.stat().st_size / 1024
        tree.add(f"📄 {file.name} [dim]({size:.1f} KB)[/dim]")

    console.print(tree)
    console.print("\n[bold green]✓ Build successful[/bold green]")

@app.command()
def all():
    """Run full build pipeline"""
    steps = [
        ("clean", "Cleaning artifacts"),
        ("lint", "Running linters"),
        ("test", "Running tests"),
        ("build", "Building distribution"),
    ]

    console.print(Panel(
        "Running full build pipeline",
        title="🚀 Build",
        border_style="cyan"
    ))

    for cmd, description in steps:
        console.print(f"\n[bold cyan]→ {description}...[/bold cyan]")

        if cmd == "clean":
            clean()
        elif cmd == "lint":
            lint()
        elif cmd == "test":
            test()
        elif cmd == "build":
            build()

    console.print("\n[bold green]✓ Build pipeline completed successfully[/bold green]")

if __name__ == "__main__":
    app()
```

---

## 5. System Monitor

Real-time system monitoring dashboard.

```python
#!/usr/bin/env python3
"""System Monitor - sysmon"""

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
import time
import psutil
from datetime import datetime

app = typer.Typer(help="System monitor")
console = Console()

def generate_dashboard():
    """Generate monitoring dashboard"""
    layout = Layout()

    # CPU info
    cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
    cpu_table = Table(title="CPU Usage", show_header=True)
    cpu_table.add_column("Core", style="cyan")
    cpu_table.add_column("Usage", style="magenta", justify="right")

    for i, usage in enumerate(cpu_percent):
        color = "green" if usage < 50 else "yellow" if usage < 80 else "red"
        cpu_table.add_row(f"Core {i}", f"[{color}]{usage:.1f}%[/{color}]")

    # Memory info
    mem = psutil.virtual_memory()
    mem_table = Table(title="Memory", show_header=True)
    mem_table.add_column("Metric", style="cyan")
    mem_table.add_column("Value", style="green", justify="right")

    mem_table.add_row("Total", f"{mem.total / 1024**3:.2f} GB")
    mem_table.add_row("Used", f"{mem.used / 1024**3:.2f} GB")
    mem_table.add_row("Available", f"{mem.available / 1024**3:.2f} GB")
    mem_table.add_row("Percent", f"{mem.percent}%")

    # Combine
    layout.split_column(
        Layout(cpu_table, name="cpu"),
        Layout(mem_table, name="memory"),
    )

    return Panel(
        layout,
        title=f"System Monitor - {datetime.now().strftime('%H:%M:%S')}",
        border_style="cyan"
    )

@app.command()
def watch(
    interval: float = typer.Option(1.0, help="Update interval in seconds"),
    duration: int = typer.Option(60, help="Duration in seconds"),
):
    """Watch system metrics in real-time"""

    start_time = time.time()

    with Live(generate_dashboard(), refresh_per_second=4) as live:
        while time.time() - start_time < duration:
            time.sleep(interval)
            live.update(generate_dashboard())

    console.print("[green]✓[/green] Monitoring complete")

if __name__ == "__main__":
    app()
```

---

## 6. Code Generator

Code scaffolding tool.

```python
#!/usr/bin/env python3
"""Code Generator - codegen"""

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.syntax import Syntax
from pathlib import Path
from typing import List

app = typer.Typer(help="Code generator")
console = Console()

@app.command()
def component(
    name: str = typer.Argument(..., help="Component name"),
    template: str = typer.Option("default", help="Template to use"),
):
    """Generate component files"""

    # Generate files
    files = {
        f"{name}.py": f'''"""
{name} component
"""

class {name}:
    """Main {name} class"""

    def __init__(self):
        pass

    def run(self):
        """Run the component"""
        pass
''',
        f"test_{name}.py": f'''"""
Tests for {name}
"""

import pytest
from {name} import {name}

def test_{name.lower()}_init():
    """Test {name} initialization"""
    obj = {name}()
    assert obj is not None

def test_{name.lower()}_run():
    """Test {name} run method"""
    obj = {name}()
    obj.run()
''',
    }

    # Show preview
    console.print(Panel(
        f"[bold]Generating component: {name}[/bold]\n\n"
        f"Files to create:\n" +
        "\n".join(f"  • {f}" for f in files.keys()),
        title="Component Generator",
        border_style="cyan"
    ))

    if not Confirm.ask("\nProceed with generation?"):
        console.print("[yellow]Cancelled[/yellow]")
        return

    # Create files
    for filename, content in files.items():
        path = Path(filename)

        if path.exists():
            if not Confirm.ask(f"[yellow]{filename} exists. Overwrite?[/yellow]"):
                continue

        path.write_text(content)
        console.print(f"[green]✓[/green] Created {filename}")

    console.print("\n[bold green]✓ Component generated successfully[/bold green]")

@app.command()
def preview(
    name: str = typer.Argument(..., help="Component name"),
):
    """Preview generated code without creating files"""

    content = f'''"""
{name} component
"""

class {name}:
    """Main {name} class"""

    def __init__(self):
        pass

    def run(self):
        """Run the component"""
        pass
'''

    syntax = Syntax(content, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Preview: {name}.py", border_style="cyan"))

if __name__ == "__main__":
    app()
```

---

These examples demonstrate real-world patterns including:
- State management (migrations, configuration)
- Batch processing with error handling
- Caching and optimization
- Interactive workflows
- Real-time monitoring
- Code generation and templating
