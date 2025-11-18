# Technology Stack

## Language & Version
- Python 3.12+ (required)
- Version managed via `.python-version` file

## Build System
- Uses `pyproject.toml` for project configuration (PEP 621 standard)
- Package name: `asana-tools`
- **Package manager: UV only** - no pip, no manual virtualenv activation
- Console command registered as `aa` via `[project.scripts]`

## Common Commands
```bash
# Run the console command (after uv sync)
uv run aa

# Install/sync dependencies and scripts
uv sync

# Add new dependencies
uv add <package-name>

# Run any Python command
uv run python <script.py>

# Build for publishing
uv build
```

## Dependencies
All dependencies managed through UV. Add new dependencies using `uv add` command, which automatically updates `pyproject.toml`.
