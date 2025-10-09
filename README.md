# sisyphus

A Python project built with anyio, supporting both asyncio and trio backends.

## Installation

```bash
uv sync
```

## Running the Project

### Quick start (recommended)

```bash
uv run sisyphus
```

### Alternative: Run as module

```bash
uv run python -m sisyphus
```

Both commands execute the main entry point defined in `sisyphus/__main__.py`.

## Development

### Type checking

```bash
uv run basedpyright
```

### Linting

```bash
uv run ruff check
```

### Formatting

```bash
uv run ruff format
```

### Testing

Quick start (recommended):

```bash
uv run test
```

Alternative (direct pytest):

```bash
uv run pytest
```

Tests automatically support async with `pytest.mark.anyio` and work with both asyncio (uvloop) and trio backends.

Run tests with verbose output:

```bash
uv run pytest -v
```

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

## Tech Stack

- **Python**: 3.12.x
- **Async Runtime**: anyio (supports asyncio with uvloop and trio)
- **Testing**: pytest + pytest-anyio
- **Type Checking**: basedpyright
- **Linting & Formatting**: ruff
- **Package Manager**: uv
