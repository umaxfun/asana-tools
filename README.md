# Asana Auto-ID

Automatic human-readable ID assignment for Asana tasks and subtasks.

## Overview

`aa` is a command-line tool that automatically assigns short, human-readable IDs to your Asana tasks. It adds prefixes like `PRJ-5` or `PRJ-5-1` to task names, making them easier to reference in discussions, documentation, and team communication.

**Key Features:**
- 🔢 Automatic ID assignment with hierarchical numbering
- 🔄 Preserves existing IDs and detects conflicts
- 🌳 Supports nested subtask hierarchies (e.g., `PRJ-5-2-3`)
- 🚀 Async processing for fast performance
- 🔍 Dry-run mode to preview changes
- 📦 Multiple project support from a single config

## Installation

### Prerequisites
- Python 3.12 or higher
- [UV package manager](https://docs.astral.sh/uv/)

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install aa

```bash
# Clone the repository
git clone <repository-url>
cd asana-tools

# Sync dependencies and install the command
uv sync

# Verify installation
uv run aa --help
```

## Quick Start

### 1. Initialize Configuration

Run the interactive setup to create your configuration file:

```bash
uv run aa init
```

This will:
- Prompt for your Asana Personal Access Token (hidden input)
- Fetch all your active projects from Asana
- Create `.aa.yml` with all projects and helpful comments

**Alternative:** Create a template manually:

```bash
uv run aa init --force
```

### 2. Scan Your Projects

Scan your projects to build the ID cache:

```bash
uv run aa scan
```

This creates `.aa.cache.yaml` with the current state of IDs in your projects.

### 3. Assign IDs

Preview what changes will be made:

```bash
uv run aa update --dry-run
```

Apply the changes:

```bash
uv run aa update
```

## Usage

### Commands

#### `aa init`

Initialize configuration file.

```bash
# Interactive mode (default) - fetches your projects
uv run aa init

# Create template file
uv run aa init --force

# Specify custom config path
uv run aa init --config my-config.yml
```

#### `aa scan`

Scan projects and update cache with existing IDs.

```bash
# Scan all projects
uv run aa scan

# Scan specific project
uv run aa scan --project PRJ

# Ignore conflicts and update cache anyway
uv run aa scan --ignore-conflicts

# Verbose output
uv run aa scan -v

# Very verbose (includes HTTP logs)
uv run aa scan -vv
```

#### `aa update`

Assign IDs to tasks without them.

```bash
# Preview changes (dry-run)
uv run aa update --dry-run

# Update all projects
uv run aa update

# Update specific project
uv run aa update --project PRJ

# Ignore conflicts during scan
uv run aa update --ignore-conflicts

# Verbose output
uv run aa update -v
```

### Global Options

All commands support these global options:

- `--config TEXT` - Path to config file (default: `.aa.yml`)
- `-v, --verbose` - Increase verbosity (use `-vv` for debug level)
- `--help` - Show help message

## Configuration Format

### `.aa.yml`

The configuration file defines your Asana token and projects:

```yaml
asana_token: 'your-personal-access-token'
interactive: false
projects:
  # Project Name
  # https://app.asana.com/0/1234567890
  - code: PRJ  # 2-5 uppercase letters
    asana_id: '1234567890'
  
  # Another Project
  # https://app.asana.com/0/9876543210
  - code: TSK
    asana_id: '9876543210'
```

**Fields:**
- `asana_token` (required) - Your Asana Personal Access Token
- `interactive` (optional) - Set to `false` to disable interactive prompts
- `projects` (required) - List of projects to manage
  - `code` (required) - 2-5 uppercase letters, used as ID prefix
  - `asana_id` (required) - Asana project ID (numeric string)

**Getting Your Personal Access Token:**
1. Go to [Asana Developer Console](https://app.asana.com/0/developer-console)
2. Click "Create new token"
3. Copy the token and paste it in your config

## Cache Format

### `.aa.cache.yaml`

The cache file tracks the last assigned IDs for each project:

```yaml
projects:
  PRJ:
    last_root: 42        # Last root task ID (PRJ-42)
    subtasks:
      '5': 3             # PRJ-5-3 is the last subtask of PRJ-5
      '12': 7            # PRJ-12-7 is the last subtask of PRJ-12
      '12-2': 4          # PRJ-12-2-4 is the last subtask of PRJ-12-2
  TSK:
    last_root: 15
    subtasks: {}
```

**Structure:**
- `projects` - Dictionary keyed by project code
  - `last_root` - Highest root task number assigned
  - `subtasks` - Dictionary mapping parent IDs to their last subtask number
    - Key format: `"5"` for root task PRJ-5, `"12-2"` for subtask PRJ-12-2
    - Value: Last subtask number assigned to that parent

**Note:** This file is automatically managed by `aa scan` and `aa update`. You typically don't need to edit it manually.

## ID Format and Hierarchy

### ID Structure

IDs follow a hierarchical pattern:

- **Root tasks:** `CODE-N` (e.g., `PRJ-5`)
- **Subtasks:** `CODE-N-M` (e.g., `PRJ-5-1`)
- **Nested subtasks:** `CODE-N-M-K` (e.g., `PRJ-5-1-2`)
- **Deeper nesting:** `CODE-N-M-K-...` (unlimited depth)

Where:
- `CODE` = Project code (2-5 uppercase letters)
- `N, M, K` = Sequential numbers starting from 1

### Example Hierarchy

```
PRJ-1: Implement authentication
├── PRJ-1-1: Design login flow
├── PRJ-1-2: Create user model
│   ├── PRJ-1-2-1: Add validation
│   └── PRJ-1-2-2: Write tests
└── PRJ-1-3: Build API endpoints

PRJ-2: Setup CI/CD
├── PRJ-2-1: Configure GitHub Actions
└── PRJ-2-2: Add deployment scripts

PRJ-3: Documentation
```

### How IDs Are Assigned

1. **Root tasks** get sequential numbers: `PRJ-1`, `PRJ-2`, `PRJ-3`, ...
2. **Subtasks** inherit parent ID and add their own number: `PRJ-1-1`, `PRJ-1-2`, ...
3. **Nested subtasks** continue the pattern: `PRJ-1-2-1`, `PRJ-1-2-2`, ...
4. **Existing IDs** are preserved - tasks with IDs are skipped
5. **Counters** are tracked in the cache to ensure no duplicates

### Task Name Format

IDs are prepended to task names:

```
Before: "Implement user authentication"
After:  "PRJ-5 Implement user authentication"

Before: "Add validation"
After:  "PRJ-5-2 Add validation"
```

## Workflow

### Typical Workflow

1. **Initial Setup**
   ```bash
   uv run aa init              # Create config with your projects
   uv run aa scan              # Build initial cache
   uv run aa update --dry-run  # Preview changes
   uv run aa update            # Apply IDs
   ```

2. **Regular Usage**
   ```bash
   # When you add new tasks in Asana:
   uv run aa update            # Assign IDs to new tasks
   ```

3. **Adding New Projects**
   - Edit `.aa.yml` to add the new project
   - Run `uv run aa scan --project NEW` to initialize cache
   - Run `uv run aa update --project NEW` to assign IDs

### Conflict Handling

**What is a conflict?**
- An ID exists in Asana that's higher than the cached value
- Duplicate IDs found in different tasks

**When conflicts occur:**
```bash
# Default: scan/update stops with an error
uv run aa scan
# Error: Conflict detected! Task "PRJ-50" found but cache shows last_root: 42

# Option 1: Fix manually (update cache or rename tasks)
# Option 2: Ignore and update cache to match Asana
uv run aa scan --ignore-conflicts
```

**Best practice:** Investigate conflicts before using `--ignore-conflicts` to ensure no IDs were assigned outside of `aa`.

## Advanced Usage

### Multiple Projects

Process all projects at once:
```bash
uv run aa update
```

Process specific project:
```bash
uv run aa update --project PRJ
```

### Custom Config Location

```bash
uv run aa --config ~/my-configs/asana.yml scan
uv run aa --config ~/my-configs/asana.yml update
```

### Debugging

Enable verbose logging:
```bash
# INFO level
uv run aa scan -v

# DEBUG level (includes HTTP requests)
uv run aa scan -vv
```

### Dry-Run Mode

Always preview changes before applying:
```bash
uv run aa update --dry-run
```

This shows:
- Which tasks will get IDs
- What the new names will be
- No changes are made to Asana or cache

## Troubleshooting

### "Config file not found"

Make sure you've run `uv run aa init` or created `.aa.yml` manually.

### "Invalid token" or 401 errors

Your Asana token may be expired or invalid. Generate a new token and update `.aa.yml`.

### "Conflict detected"

Someone may have manually added IDs or the cache is out of sync. Options:
1. Review the conflicting tasks in Asana
2. Update the cache manually if needed
3. Use `--ignore-conflicts` to auto-update cache

### Tasks not getting IDs

Check that:
- Tasks don't already have IDs (they're skipped)
- You're running `update`, not just `scan`
- You're not in `--dry-run` mode

### Rate limiting

Asana API has rate limits (1500 requests/minute). The tool includes automatic retry logic with exponential backoff.

## Development

### Project Structure

```
asana-tools/
├── aa/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # Main CLI entry point
│   ├── commands/           # CLI commands
│   │   ├── init.py
│   │   ├── scan.py
│   │   └── update.py
│   ├── core/               # Business logic
│   │   ├── asana_client.py
│   │   ├── id_manager.py
│   │   └── task_processor.py
│   ├── models/             # Data models
│   │   ├── config.py
│   │   ├── cache.py
│   │   └── task.py
│   └── utils/              # Utilities
│       ├── config_loader.py
│       └── cache_manager.py
├── .aa.yml                 # Config file (gitignored)
├── .aa.cache.yaml          # Cache file (gitignored)
├── pyproject.toml          # Project metadata
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=aa
```

### Adding Dependencies

```bash
uv add <package-name>
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
