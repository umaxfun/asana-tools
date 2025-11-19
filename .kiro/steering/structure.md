# Project Structure

## Root Directory
```
asana-tools/
├── .git/              # Git repository
├── .kiro/             # Kiro configuration and specs
│   ├── specs/         # Feature specifications
│   │   └── asana-auto-id/  # Main feature spec
│   └── steering/      # AI assistant guidance documents
├── .vscode/           # VS Code settings
├── .venv/             # Virtual environment (gitignored)
├── aa/                # Main application package
│   ├── __init__.py
│   ├── __main__.py    # Entry point for `aa` command
│   ├── cli.py         # Main CLI group with Click
│   ├── commands/      # CLI command implementations
│   │   ├── init.py    # aa init command
│   │   ├── scan.py    # aa scan command
│   │   ├── update.py  # aa update command
│   │   ├── validate.py
│   │   ├── test_id.py
│   │   ├── cache_info.py
│   │   └── list_tasks.py
│   ├── core/          # Business logic
│   │   ├── asana_client.py   # Async Asana API client
│   │   ├── id_manager.py     # ID generation and management
│   │   └── task_processor.py # Task hierarchy processing
│   ├── models/        # Pydantic data models
│   │   ├── config.py  # Config validation models
│   │   ├── cache.py   # Cache data models
│   │   └── task.py    # Asana task models
│   └── utils/         # Utility modules
│       ├── config_loader.py  # Config loading and validation
│       └── cache_manager.py  # Cache file management
├── .aa.yml            # User config file (gitignored)
├── .aa.cache.yaml     # Cache file (gitignored)
├── .gitignore         # Git ignore patterns
├── .python-version    # Python version specification (3.12)
├── pyproject.toml     # Project metadata and dependencies
├── main.py            # Legacy entry point (deprecated)
└── README.md          # Project documentation
```

## Architecture Layers

1. **CLI Layer** (`cli.py`, `commands/`) - User interface, command parsing
2. **Core Layer** (`core/`) - Business logic for ID management and task processing
3. **API Layer** (`core/asana_client.py`) - Asana API integration
4. **Data Layer** (`models/`, `utils/`) - Data models, config, and cache management

## Conventions

- Modular structure with clear separation of concerns
- Async/await throughout for I/O operations
- Pydantic models for all data validation
- Virtual environment in `.venv/` (gitignored)
- User files (`.aa.yml`, `.aa.cache.yaml`) are gitignored
- Python cache and build artifacts excluded via `.gitignore`

## Code Organization

- Entry point: `aa/__main__.py` (invoked via `uv run aa`)
- Console command: `aa` (registered in pyproject.toml)
- All commands use async/await pattern
- Click framework for CLI with command groups
- HTTPX for async HTTP requests to Asana API
