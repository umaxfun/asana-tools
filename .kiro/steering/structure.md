# Project Structure

## Root Directory
```
asana-tools/
├── .git/              # Git repository
├── .kiro/             # Kiro configuration and specs
│   ├── specs/         # Feature specifications
│   └── steering/      # AI assistant guidance documents
├── .vscode/           # VS Code settings
├── .gitignore         # Git ignore patterns
├── .python-version    # Python version specification (3.12)
├── pyproject.toml     # Project metadata and dependencies
├── main.py            # Main entry point
└── README.md          # Project documentation
```

## Conventions
- Python source files at root level (flat structure for now)
- Virtual environment in `.venv/` (gitignored)
- Python cache and build artifacts excluded via `.gitignore`

## Code Organization
- Entry point: `main.py` with `main()` function
- Console command: `aa` (registered in pyproject.toml)
- Standard Python `if __name__ == "__main__"` pattern for executables
