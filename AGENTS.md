# sisyphus

## User's Initial Requirements

Basic Python project setup:
- Python 3.12 based
- anyio based (use anyio with asyncio and trio support)
- Use pytest-anyio for testing
- Apply spray project style pyproject.toml configuration
- Auto async support with pytest.mark.anyio
- Do not install pytest-xdist yet
- Setup basic project structure only

## Tech Stack

### Core Dependencies
- **Python**: 3.12.x
- **Async Runtime**: anyio (supports both asyncio with uvloop and trio)
- **Testing**: pytest + pytest-anyio

### Development Tools
- **Linting & Formatting**: ruff
- **Type Checking**: basedpyright
- **Package Manager**: uv

### Notable Features
1. **Async-first design**: All tests automatically support async with `pytest.mark.anyio`
2. **Multi-backend support**: Works with both asyncio (uvloop) and trio backends
3. **No pytest-xdist**: Parallel test execution not yet configured
4. **Spray-style configuration**: pyproject.toml follows spray project's configuration style
   - Strict type checking (basedpyright standard mode)
   - Code quality checks with Ruff (including ANN001, ASYNC, etc.)

## Project Structure

```
sisyphus/
├── sisyphus/           # Main package
│   ├── __init__.py
│   ├── __main__.py     # Entry point
│   ├── main.py         # Main logic
│   ├── conftest.py     # Pytest configuration
│   └── tests/          # Test directory
│       ├── __init__.py
│       └── test_main__print_hello_world.py
├── pyproject.toml      # Project configuration
├── README.md           # Project documentation
└── .python-version     # Python version pinning (3.12)
```

### Code Style Guide

1. **Type Hints**: Type hints required for all function parameters and return values (ANN001)
2. **Quotes**: Use double quotes for all strings
3. **Test Style**:
   - Use Given-When-Then pattern (marked with comments)
   - Use `pytestmark = [pytest.mark.anyio]` for async test support
   - pytest fixtures use parentheses
   - pytest marks use parentheses
4. **Async**: async functions are automatically handled by pytest-anyio (no separate decorator needed per test)

### Running the Project

Quick start (recommended):

```bash
uv run sisyphus
```

Alternative (run as module):

```bash
uv run python -m sisyphus
```

Both commands execute the entry point defined in `sisyphus/__main__.py`. The project uses `[project.scripts]` in pyproject.toml for the `sisyphus` command.

### Running Tests

Quick start (recommended):

```bash
uv run test
```

Alternative (direct pytest):

```bash
uv run pytest
```

- Automatic async test support with pytest-anyio
- Supports both asyncio and trio backends
- Warnings disabled
- Log level: ERROR
- Default fixture scope: function

### Development Workflow

1. **Write Code**: Work in sisyphus/ directory
2. **Type Check**: `uv run basedpyright`
3. **Lint Check**: `uv run ruff check`
4. **Format**: `uv run ruff format`
5. **Test**: `uv run pytest`
