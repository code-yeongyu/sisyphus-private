#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "typer[all]>=0.9.0",
#     "rich>=13.0.0",
# ]
# ///
"""
CLI Project Initializer

Creates a new Python CLI project with Typer + Rich setup.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.tree import Tree

app = typer.Typer()
console = Console()


def create_directory_structure(project_name: str, base_path: Path) -> dict[str, Path]:
    """Create project directory structure"""
    paths = {
        "root": base_path / project_name,
        "package": base_path / project_name / project_name,
        "commands": base_path / project_name / project_name / "commands",
        "utils": base_path / project_name / project_name / "utils",
        "tests": base_path / project_name / "tests",
    }

    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    return paths


def create_init_files(paths: dict[str, Path]) -> None:
    """Create __init__.py files"""
    init_files = [
        paths["package"] / "__init__.py",
        paths["commands"] / "__init__.py",
        paths["utils"] / "__init__.py",
        paths["tests"] / "__init__.py",
    ]

    version_content = '__version__ = "0.1.0"\n'

    for init_file in init_files:
        if init_file == paths["package"] / "__init__.py":
            init_file.write_text(version_content)
        else:
            init_file.write_text("")


def create_cli_file(project_name: str, paths: dict[str, Path]) -> None:
    """Create main CLI file"""
    content = f'''"""
{project_name} - Main CLI Application
"""

import typer
from {project_name} import __version__
from {project_name}.utils.output import console
from rich.panel import Panel

app = typer.Typer(
    name="{project_name}",
    help="{project_name.replace("_", " ").title()} CLI Application",
    add_completion=True,
)


def version_callback(value: bool):
    """Show version and exit"""
    if value:
        console.print(f"{project_name} version [cyan]{{__version__}}[/cyan]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    )
):
    """
    {project_name.replace("_", " ").title()} CLI Application

    Use --help with any command for more information.
    """
    pass


@app.command()
def hello(
    name: str = typer.Option("World", help="Name to greet"),
    uppercase: bool = typer.Option(False, help="Uppercase the greeting"),
):
    """
    Greet someone with style!

    Example:
        {project_name} hello --name Alice
        {project_name} hello --name Bob --uppercase
    """
    greeting = f"Hello, {{name}}!"

    if uppercase:
        greeting = greeting.upper()

    console.print(Panel(
        f"[bold magenta]{{greeting}}[/bold magenta]",
        title="Greeting",
        border_style="green"
    ))


if __name__ == "__main__":
    app()
'''

    cli_file = paths["package"] / "cli.py"
    cli_file.write_text(content)


def create_main_file(project_name: str, paths: dict[str, Path]) -> None:
    """Create __main__.py file"""
    content = f'''"""
Entry point for {project_name} CLI
"""

from {project_name}.cli import app

if __name__ == "__main__":
    app()
'''

    main_file = paths["package"] / "__main__.py"
    main_file.write_text(content)


def create_output_utils(project_name: str, paths: dict[str, Path]) -> None:
    """Create output utilities with Rich theme"""
    content = '''"""
Rich console and output utilities
"""

from rich.console import Console
from rich.theme import Theme

# Custom theme for consistent styling
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


def print_success(message: str):
    """Print success message"""
    console.print(f"[success]✓[/success] {message}")


def print_error(message: str):
    """Print error message"""
    console.print(f"[error]✗[/error] {message}")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"[warning]⚠[/warning] {message}")


def print_info(message: str):
    """Print info message"""
    console.print(f"[info]ℹ[/info] {message}")


def print_header(text: str):
    """Print styled header"""
    console.print(f"\\n[bold white on blue] {text} [/bold white on blue]\\n")
'''

    output_file = paths["utils"] / "output.py"
    output_file.write_text(content)


def create_example_command(project_name: str, paths: dict[str, Path]) -> None:
    """Create example command module"""
    content = f'''"""
Example command group
"""

import typer
from {project_name}.utils.output import console, print_success
from rich.table import Table

app = typer.Typer(help="Example commands")


@app.command()
def list():
    """List example items"""
    table = Table(title="Example Items", show_header=True, header_style="bold magenta")

    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Status", justify="center")

    # Sample data
    items = [
        ("1", "Item One", "✓ Active"),
        ("2", "Item Two", "✓ Active"),
        ("3", "Item Three", "⏸ Inactive"),
    ]

    for item_id, name, status in items:
        table.add_row(item_id, name, status)

    console.print(table)


@app.command()
def create(name: str = typer.Argument(..., help="Item name")):
    """Create a new item"""
    print_success(f"Created item: {{name}}")


if __name__ == "__main__":
    app()
'''

    command_file = paths["commands"] / "example.py"
    command_file.write_text(content)


def create_pyproject_toml(project_name: str, paths: dict[str, Path], author_name: str, author_email: str) -> None:
    """Create pyproject.toml"""
    content = f"""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "{project_name.replace("_", " ").title()} CLI Application"
readme = "README.md"
authors = [
    {{name = "{author_name}", email = "{author_email}"}}
]
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
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

[project.scripts]
{project_name} = "{project_name}.cli:app"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["{project_name}*"]

[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.ruff]
line-length = 88
target-version = "py38"
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --cov={project_name} --cov-report=term-missing"
"""

    pyproject_file = paths["root"] / "pyproject.toml"
    pyproject_file.write_text(content)


def create_readme(project_name: str, paths: dict[str, Path]) -> None:
    """Create README.md"""
    content = f"""# {project_name.replace("_", " ").title()}

A beautiful CLI application built with Typer and Rich.

## Installation

### Development

```bash
# Clone the repository
git clone <repository-url>
cd {project_name}

# Install in development mode
pip install -e ".[dev]"
```

### From PyPI (after publishing)

```bash
pip install {project_name}
```

## Usage

### Basic Commands

```bash
# Show help
{project_name} --help

# Show version
{project_name} --version

# Greet someone
{project_name} hello --name Alice

# List example items
{project_name} example list

# Create an item
{project_name} example create "My Item"
```

## Development

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov={project_name} --cov-report=html
```

### Code Formatting

```bash
black .
```

### Linting

```bash
ruff check .
```

## Project Structure

```
{project_name}/
├── {project_name}/
│   ├── __init__.py          # Version info
│   ├── __main__.py          # Entry point
│   ├── cli.py               # Main CLI logic
│   ├── commands/
│   │   ├── __init__.py
│   │   └── example.py       # Example command group
│   └── utils/
│       ├── __init__.py
│       └── output.py        # Rich console & styling
├── tests/
│   ├── __init__.py
│   └── test_cli.py          # Tests
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## Features

- ✅ Beautiful terminal output with Rich
- ✅ Type-safe CLI with Typer
- ✅ Organized command structure
- ✅ Consistent styling and themes
- ✅ Comprehensive tests
- ✅ Modern Python packaging

## License

MIT License
"""

    readme_file = paths["root"] / "README.md"
    readme_file.write_text(content)


def create_test_file(project_name: str, paths: dict[str, Path]) -> None:
    """Create test file"""
    content = f'''"""
Tests for {project_name} CLI
"""

import pytest
from typer.testing import CliRunner
from {project_name}.cli import app

runner = CliRunner()


def test_version():
    """Test --version flag"""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "{project_name}" in result.stdout
    assert "0.1.0" in result.stdout


def test_help():
    """Test --help flag"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "{project_name}" in result.stdout.lower()


def test_hello_default():
    """Test hello command with default name"""
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.stdout


def test_hello_with_name():
    """Test hello command with custom name"""
    result = runner.invoke(app, ["hello", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Alice" in result.stdout


def test_hello_uppercase():
    """Test hello command with uppercase flag"""
    result = runner.invoke(app, ["hello", "--name", "Bob", "--uppercase"])
    assert result.exit_code == 0
    assert "BOB" in result.stdout


# Add more tests as you develop your CLI
'''

    test_file = paths["tests"] / "test_cli.py"
    test_file.write_text(content)


def create_gitignore(paths: dict[str, Path]) -> None:
    """Create .gitignore"""
    content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
.env
"""

    gitignore_file = paths["root"] / ".gitignore"
    gitignore_file.write_text(content)


def show_project_tree(project_name: str, paths: dict[str, Path]) -> None:
    """Display created project structure"""
    tree = Tree(f"📁 [bold cyan]{project_name}[/bold cyan]")

    # Package directory
    package = tree.add(f"📁 {project_name}")
    package.add("📄 __init__.py")
    package.add("📄 __main__.py")
    package.add("📄 cli.py")

    commands = package.add("📁 commands")
    commands.add("📄 __init__.py")
    commands.add("📄 example.py")

    utils = package.add("📁 utils")
    utils.add("📄 __init__.py")
    utils.add("📄 output.py")

    # Tests
    tests = tree.add("📁 tests")
    tests.add("📄 __init__.py")
    tests.add("📄 test_cli.py")

    # Root files
    tree.add("📄 pyproject.toml")
    tree.add("📄 README.md")
    tree.add("📄 .gitignore")

    console.print(tree)


@app.command()
def main(
    project_name: str = typer.Argument(..., help="Name of the CLI project (use snake_case)"),
    path: Path | None = typer.Option(
        None, help="Directory where project will be created (default: current directory)"
    ),
    author_name: str | None = typer.Option(None, help="Author name for pyproject.toml"),
    author_email: str | None = typer.Option(None, help="Author email for pyproject.toml"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing directory"),
) -> None:
    """
    Initialize a new Python CLI project with Typer + Rich.

    Creates a complete project structure with:
    - Main CLI application with example commands
    - Rich-themed output utilities
    - Test suite
    - Modern pyproject.toml configuration
    - README and .gitignore

    Example:
        python init_cli.py my_awesome_cli
        python init_cli.py my_tool --path ~/projects
        python init_cli.py my_cli --author-name "John Doe" --author-email "john@example.com"
    """

    # Validate project name
    if not project_name.replace("_", "").replace("-", "").isalnum():
        console.print("[error]Project name must contain only letters, numbers, hyphens, and underscores[/error]")
        raise typer.Exit(1)

    # Replace hyphens with underscores for Python package name
    project_name = project_name.replace("-", "_")

    # Determine base path
    base_path = path if path else Path.cwd()

    # Check if directory exists
    project_path = base_path / project_name
    if project_path.exists() and not force:
        console.print(f"[error]Directory '{project_path}' already exists. Use --force to overwrite.[/error]")
        raise typer.Exit(1)

    # Get author info interactively if not provided
    author_name = author_name or Prompt.ask("Author name", default="Your Name")
    author_email = author_email or Prompt.ask("Author email", default="you@example.com")

    # Show what will be created
    console.print(
        Panel(
            f"[bold]Creating CLI project:[/bold] {project_name}\n"
            f"[dim]Location:[/dim] {project_path}\n"
            f"[dim]Author:[/dim] {author_name} <{author_email}>",
            title="🚀 CLI Project Initializer",
            border_style="cyan",
        )
    )

    if not Confirm.ask("\nProceed with creation?", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        raise typer.Exit()

    try:
        # Create project
        console.print("\n[cyan]Creating project structure...[/cyan]")
        paths = create_directory_structure(project_name, base_path)

        console.print("[cyan]Creating files...[/cyan]")
        create_init_files(paths)
        create_cli_file(project_name, paths)
        create_main_file(project_name, paths)
        create_output_utils(project_name, paths)
        create_example_command(project_name, paths)
        create_pyproject_toml(project_name, paths, author_name, author_email)
        create_readme(project_name, paths)
        create_test_file(project_name, paths)
        create_gitignore(paths)

        # Show success
        console.print("\n[bold green]✓ Project created successfully![/bold green]\n")
        show_project_tree(project_name, paths)

        # Show next steps
        console.print(
            Panel(
                f"[bold]Next steps:[/bold]\n\n"
                f"1. [cyan]cd {project_name}[/cyan]\n"
                f'2. [cyan]pip install -e ".[dev]"[/cyan]  # Install in development mode\n'
                f"3. [cyan]{project_name} --help[/cyan]  # Try your CLI!\n"
                f"4. [cyan]pytest[/cyan]  # Run tests\n\n"
                f"[dim]Edit {project_name}/cli.py to add your commands[/dim]",
                title="🎉 Ready to Go",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(
            Panel(f"[red bold]Error creating project:[/red bold]\n\n{str(e)}", title="❌ Error", border_style="red")
        )
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
