---
name: python-script-writer
description: Create standalone, self-contained Python scripts with uv shebang and PEP 723 inline script metadata. Dependencies are embedded using inline metadata, making scripts portable and executable anywhere without setup. Use when creating CLI tools, utilities, or scripts that need to be distributed as single executable files.
---

# Python Script Writer

## Overview

Create portable, single-file Python scripts that embed their dependencies using PEP 723 inline script metadata and uv shebang. These scripts are self-contained and can run anywhere without complex setup or virtual environment configuration.

## Template Structure

Every script follows this structure:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.12"
# dependencies = [
#     "package1",
#     "package2>=1.0.0",
#     "package3~=2.1",
# ]
# ///

# Your Python code here
import package1
import package2

def main():
    # Implementation
    pass

if __name__ == "__main__":
    main()
```

### Key Components

1. **Shebang**: `#!/usr/bin/env -S uv run --script`
   - Enables direct execution with uv
   - Must be the first line

2. **PEP 723 Metadata Block**: Between `# /// script` and `# ///`
   - `requires-python`: Python version requirement (e.g., `"~=3.12"`, `">=3.11"`)
   - `dependencies`: List of package dependencies with optional version specifiers
   - Use standard PEP 440 version specifiers: `==`, `>=`, `~=`, etc.

3. **Script Content**: Regular Python code below the metadata block

## Creating a Script

### Step 1: Write the Script

Create a Python file with the template structure:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.12"
# dependencies = [
#     "typer",
#     "rich",
# ]
# ///

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def hello(name: str):
    console.print(f"[bold green]Hello {name}![/bold green]")

if __name__ == "__main__":
    app()
```

### Step 2: Make Executable

After creating the script, always run:

```bash
chmod +x script_name.py
```

This enables direct execution: `./script_name.py` instead of `python script_name.py`

### Step 3: Execute

Run the script directly:

```bash
./script_name.py --help
./script_name.py argument
```

uv automatically:
- Creates an isolated environment
- Installs dependencies
- Executes the script

## CRITICAL PATTERNS (MUST FOLLOW)

⚠️ **These patterns are MANDATORY for all scripts using Rich and asyncio.**

Violations will result in broken output, race conditions, or poor performance.

---

### 🔴 Pattern 1: Shared Rich Console

**RULE:** Use a single `Console()` instance for ALL output in your script.

**WHY:**
- Progress bars and prints must share the same console
- Multiple consoles cause overlapping/corrupted terminal output
- Inconsistent styling and formatting across outputs

**HOW:**
```python
# ✓ CORRECT - Module-level shared console
from rich.console import Console

console = Console()  # Single instance

# Use everywhere
console.print("Starting...")
with Progress(console=console) as progress:
    console.print("Processing...")  # Same console!
```

```python
# ✗ WRONG - Multiple consoles
console1 = Console()
console2 = Console()

with Progress() as progress:  # Creates yet another console
    console1.print("...")  # Different consoles = broken output!
```

**VIOLATION CAUSES:**
- Broken progress bar rendering
- Text appearing in wrong order
- Terminal artifacts and corruption
- Inconsistent color/style output

---

### 🔴 Pattern 2: Rich Progress for State Tracking

**RULE:** ALWAYS use `Progress` for tracking multi-step operations.

NEVER use manual counters, print-based progress, or custom indicators.

**WHY:**
- Automatic time tracking (elapsed time, ETA)
- Consistent UX across all scripts
- Proper terminal rendering without corruption
- Professional appearance

**DEFAULT PATTERN (USE THIS):**
```python
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()

def process_items(items: list[str]) -> None:
    with Progress(console=console) as progress:
        task: TaskID = progress.add_task(
            "[cyan]Processing items...",
            total=len(items)
        )

        for idx, item in enumerate(items, 1):
            # Your processing logic
            result = process_single_item(item)

            # Show what was processed using shared console
            console.print(f"[green]✓[/green] Processed: {item} -> {result}")

            # Update progress
            progress.update(
                task,
                advance=1,
                description=f"[cyan]Processing items... ({idx}/{len(items)})"
            )
```

**DEFAULT PROGRESS BAR INCLUDES (AUTOMATIC):**
- 📊 Progress bar (visual indicator)
- 📈 Percentage (auto-calculated)
- 🔢 Count (N/Total processed)
- ⏱️ Elapsed time
- ⏳ Estimated time remaining (ETA)

**KEY POINTS:**
- Use `Progress(console=console)` - pass shared console
- Use `TaskID` type hint for task variable
- Call `progress.update()` with `advance=1` after each item
- Update `description` to show current count

**VIOLATION CAUSES:**
- Inconsistent user experience
- Missing time estimates
- Manual progress tracking errors
- Terminal output corruption

---

### 🔴 Pattern 3: Single Print Calls with F-strings

**RULE:** Combine multiple lines into ONE print call using f-strings and triple-quotes (`"""`).

NEVER make multiple consecutive print calls for related content.

**WHY:**
- **Performance**: Reduces syscalls dramatically
- **Atomicity**: Content renders as one unit (no interleaving)
- **Readability**: Output structure is clear in code
- **Maintainability**: Easier to modify multi-line output

**CORRECT:**
```python
console.print(f"""
[cyan]━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]
[cyan]Total items: {len(items)}[/cyan]
[cyan]Status: {status}[/cyan]
[cyan]Mode: {mode}[/cyan]
[cyan]━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]
""")
```

**WRONG:**
```python
# ✗ DO NOT DO THIS
console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
console.print(f"[cyan]Total items: {len(items)}[/cyan]")
console.print(f"[cyan]Status: {status}[/cyan]")
console.print(f"[cyan]Mode: {mode}[/cyan]")
console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
```

**ADVANCED USAGE:**
```python
# Build complex output with f-strings
items_display = "\n".join(f"\t[blue]- {item}[/blue]" for item in items)

console.print(f"""
[cyan]━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]
[green]Found {len(items)} items:[/green]
{items_display}
[cyan]━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]
""")
```

**VIOLATION CAUSES:**
- Slower performance (multiple syscalls)
- Potential output interleaving in concurrent contexts
- Code bloat and redundancy
- Harder to maintain

---

### 🔴 Pattern 4: Asyncio Integration with Typer

**RULE:** When using async operations (subprocess, HTTP, concurrent tasks),
wrap them in an async function and call with `asyncio.run()`.

**WHY:**
- Typer only supports synchronous functions
- Asyncio enables parallel operations and non-blocking I/O
- Clean separation of CLI parsing and async logic
- Better performance for I/O-bound tasks

**COMPLETE PATTERN:**
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12.0", "rich>=13.0.0"]
# ///

import asyncio
import typer
from rich.console import Console
from rich.progress import Progress, TaskID

app = typer.Typer()
console = Console()

@app.command()
def main(
    branches: list[str] = typer.Argument(..., help="Branches to process"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Sync wrapper for async operations."""

    async def async_main() -> None:
        # 1. Use asyncio.create_subprocess_exec for shell commands
        proc = await asyncio.create_subprocess_exec(
            "git", "status",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        # 2. Use asyncio.gather for parallel operations
        async def fetch_pr_info(branch: str) -> dict:
            # Simulated async operation
            await asyncio.sleep(0.1)
            return {"branch": branch, "status": "ready"}

        results = await asyncio.gather(
            fetch_pr_info(branches[0]),
            fetch_pr_info(branches[1]),
            return_exceptions=True,  # Don't fail if one task fails
        )

        # 3. Use Progress for tracking with shared console
        with Progress(console=console) as progress:
            task: TaskID = progress.add_task(
                "[cyan]Processing branches...",
                total=len(branches)
            )

            for idx, branch in enumerate(branches, 1):
                # Async processing
                await process_branch(branch)

                # Update progress
                console.print(f"[green]✓[/green] Processed {branch}")
                progress.update(
                    task,
                    advance=1,
                    description=f"[cyan]Processing... ({idx}/{len(branches)})"
                )

    # 4. Run async function
    asyncio.run(async_main())

if __name__ == "__main__":
    app()
```

**KEY COMPONENTS:**

1. **asyncio.create_subprocess_exec()** for shell commands:
```python
proc = await asyncio.create_subprocess_exec(
    "command", "arg1", "arg2",
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
stdout, stderr = await proc.communicate()
```

2. **asyncio.gather()** for parallel operations:
```python
results = await asyncio.gather(
    async_task1(),
    async_task2(),
    async_task3(),
    return_exceptions=True,  # Continue if one fails
)
```

3. **asyncio.run()** to execute async function:
```python
@app.command()
def main(...) -> None:
    async def async_main() -> None:
        # All async logic here
        pass

    asyncio.run(async_main())
```

**VIOLATION CAUSES:**
- Blocking operations (no parallelism benefit)
- `SyntaxError: 'await' outside function` errors
- Typer incompatibility errors
- Lost performance benefits

---

## Best Practices (RECOMMENDED)

### Dependency Specification

**Pin major versions for stability:**
```python
# dependencies = [
#     "requests~=2.31",     # Allow patch updates: 2.31.x
#     "pydantic>=2.0.0",    # Minimum version
#     "typer==0.9.0",       # Exact version
# ]
```

**Common dependency patterns:**
- CLI tools: `typer`, `click`, `rich`, `prompt-toolkit`
- HTTP: `requests`, `httpx`
- Data: `pandas`, `polars`, `duckdb`
- Config: `pydantic`, `pyyaml`, `toml`

### Python Version

**Specify compatible version:**
```python
# requires-python = "~=3.12"   # 3.12.x
# requires-python = ">=3.11"   # 3.11 or higher
```

### Code Organization

**Keep it simple:**
- Single-file scripts work best for utilities and CLI tools
- For complex logic, consider splitting into importable modules
- Use functions and classes for organization

**CLI best practices:**
- Use `typer` or `click` for robust argument parsing
- Provide `--help` documentation
- Handle errors gracefully with try/except

---

## Common Patterns

### Complete CLI Tool with Asyncio + Progress

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12.0", "rich>=13.0.0"]
# ///

import asyncio
import typer
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel

app = typer.Typer()
console = Console()

async def process_item(item: str) -> str:
    """Simulate async processing."""
    await asyncio.sleep(0.5)
    return f"processed_{item}"

@app.command()
def main(
    items: list[str] = typer.Argument(..., help="Items to process"),
    yes: bool = typer.Option(False, "-y", "--yes"),
) -> None:
    """Process items with async operations and progress tracking."""

    async def async_main() -> None:
        # Show summary
        console.print(f"""
[cyan]━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]
[cyan]Total items: {len(items)}[/cyan]
[cyan]Mode: {'Auto' if yes else 'Interactive'}[/cyan]
[cyan]━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]
""")

        # Process with progress
        with Progress(console=console) as progress:
            task: TaskID = progress.add_task(
                "[cyan]Processing items...",
                total=len(items)
            )

            for idx, item in enumerate(items, 1):
                result = await process_item(item)

                console.print(f"[green]✓[/green] {item} -> {result}")

                progress.update(
                    task,
                    advance=1,
                    description=f"[cyan]Processing... ({idx}/{len(items)})"
                )

        # Show completion
        panel = Panel(
            f"[green]✓ Processed {len(items)} items successfully[/green]",
            title="[green]Complete[/green]",
            border_style="green",
        )
        console.print(panel)

    asyncio.run(async_main())

if __name__ == "__main__":
    app()
```

### Data Processing Script

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.12"
# dependencies = ["polars", "rich"]
# ///

import polars as pl
from rich.console import Console

console = Console()

def main():
    df = pl.read_csv("data.csv")
    result = df.filter(pl.col("value") > 100)

    console.print(f"[green]Processed {len(result)} rows[/green]")
    result.write_csv("output.csv")

if __name__ == "__main__":
    main()
```

---

## Anti-Patterns (AVOID)

### ❌ Multiple Console Instances

```python
# WRONG
console1 = Console()
console2 = Console()
with Progress() as progress:  # Creates 3rd console
    console1.print("...")
```

### ❌ Multiple Print Calls

```python
# WRONG
console.print("[cyan]Header[/cyan]")
console.print(f"[cyan]Count: {count}[/cyan]")
console.print("[cyan]Footer[/cyan]")

# CORRECT
console.print(f"""
[cyan]Header[/cyan]
[cyan]Count: {count}[/cyan]
[cyan]Footer[/cyan]
""")
```

### ❌ Blocking Subprocess Calls

```python
# WRONG - Blocking
import subprocess
result = subprocess.run(["git", "status"])

# CORRECT - Async
proc = await asyncio.create_subprocess_exec("git", "status")
```

### ❌ Manual Progress Tracking

```python
# WRONG
for i, item in enumerate(items):
    print(f"Processing {i+1}/{len(items)}...")

# CORRECT
with Progress(console=console) as progress:
    task = progress.add_task("Processing...", total=len(items))
    for item in items:
        progress.update(task, advance=1)
```

### ❌ Custom Progress Columns Without Need

```python
# WRONG - Overriding default columns
from rich.progress import SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console,
) as progress:
    pass

# CORRECT - Use default (has bar, percentage, time, ETA)
with Progress(console=console) as progress:
    pass
```

## Execution Tips

**First run**: uv downloads and caches dependencies (may take time)

**Subsequent runs**: Uses cached dependencies (fast)

**Distribution**: Share the single `.py` file - recipients only need uv installed

**Debugging**: Run with `-v` for verbose output:
```bash
uv run --script -v script.py
```

## When to Use

**Ideal for:**
- CLI utilities and tools
- Data processing scripts
- API clients
- Automation scripts
- Shareable tools for teams

**Not ideal for:**
- Large applications (use proper packages)
- Scripts requiring compiled extensions
- Projects with many files (use conventional project structure)

## Requirements

**System requirement**: uv package manager must be installed

**Installation:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
