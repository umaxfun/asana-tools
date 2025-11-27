# Asana Auto-ID

Automatic human-readable ID assignment for Asana tasks and subtasks.

## What is this?

`aa-cli` automatically adds short, readable IDs to your Asana tasks - like `PRJ-5` or `PRJ-5-1`. This makes tasks easier to reference in discussions, documentation, and team communication.

**Key Features:**

- 🔢 Automatic hierarchical ID assignment
- 🔄 Preserves existing IDs and detects conflicts
- 🌳 Supports unlimited nesting depth
- 🚀 Fast async processing
- 🔍 Dry-run mode to preview changes

## Installation

### Prerequisites

Install [UV](https://docs.astral.sh/uv/) if you don't have it:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Usage

**No installation needed!** Just use `uvx`:

```bash
uvx aa-cli@latest --help
```

## Quick Start

### 1. Initialize

Create your configuration file:

```bash
uvx aa-cli@latest init
```

This will:

- Prompt for your Asana Personal Access Token
- Fetch all your projects automatically
- Detect existing project codes from your tasks
- Create `.aa.yml` with everything configured

**Note:** For workspaces with 100+ projects, automatic code detection is skipped to avoid API rate limits. In this case, only the first project is added as an example - you can manually add your projects to the config.

**Get your token:** [Asana Developer Console](https://app.asana.com/0/developer-console) → "Create new token"

### 2. Scan

Build the ID cache from your existing tasks:

```bash
uvx aa-cli@latest scan
```

### 3. Update

Preview changes:

```bash
uvx aa-cli@latest update --dry-run
```

Apply IDs to tasks:

```bash
uvx aa-cli@latest update
```

Done! Your tasks now have IDs like `PRJ-1`, `PRJ-2`, etc.

## ID Format

IDs follow a hierarchical pattern:

```
PRJ-1: Implement authentication
├── PRJ-1-1: Design login flow
├── PRJ-1-2: Create user model
│   ├── PRJ-1-2-1: Add validation
│   └── PRJ-1-2-2: Write tests
└── PRJ-1-3: Build API endpoints

PRJ-2: Setup CI/CD
└── PRJ-2-1: Configure GitHub Actions
```

- **Root tasks:** `CODE-N` (e.g., `PRJ-5`)
- **Subtasks:** `CODE-N-M` (e.g., `PRJ-5-1`)
- **Nested:** `CODE-N-M-K` (e.g., `PRJ-5-1-2`)
- Unlimited depth supported

## Commands

### `init`

Initialize configuration:

```bash
# Interactive mode (recommended)
uvx aa-cli@latest init

# Create template only
uvx aa-cli@latest init --force
```

### `scan`

Scan projects and update cache:

```bash
# Scan all projects
uvx aa-cli@latest scan

# Scan specific project
uvx aa-cli@latest scan --project PRJ

# Ignore conflicts
uvx aa-cli@latest scan --ignore-conflicts
```

**Safety Check:** `scan` will fail if it detects "foreign" IDs (IDs from other projects) to prevent accidental duplication.

### `reset`

Remove IDs from all tasks in a project (useful for cleaning up messy projects):

```bash
# Reset specific project (requires Asana Project GID)
uvx aa-cli@latest reset --project-id 123456789

# Preview changes without applying
uvx aa-cli@latest reset --project-id 123456789 --dry-run
```

### `update`

Assign IDs to tasks:

```bash
# Preview changes
uvx aa-cli@latest update --dry-run

# Apply changes
uvx aa-cli@latest update

# Update specific project
uvx aa-cli@latest update --project PRJ
```

### Options

All commands support:

- `--config PATH` - Custom config file location
- `-v` - Verbose output (INFO level)
- `-vv` - Debug output (DEBUG level, shows API requests)
- `--help` - Show help

## Configuration

### `.aa.yml`

```yaml
asana_token: "your-personal-access-token"
projects:
  - code: PRJ # 2-5 uppercase letters
    asana_id: "1234567890"

  - code: TSK
    asana_id: "9876543210"
```

**Finding project IDs:**

There are two ways to get a project ID:

1. **From task URL (new format):**

   - Open any task in the project
   - Copy the task link
   - Find the number after `/project/`: `https://app.asana.com/.../project/123123123/task/...`
   - `123123123` is your project ID

2. **From project URL:**
   - Open the project in Asana
   - Look at the URL: `https://app.asana.com/0/123123123/...`
   - The number after `/0/` is your project ID

Or just use `uvx aa-cli@latest init` - it fetches everything automatically!

### `.aa.cache.yaml`

Automatically managed by `scan` and `update`. Tracks the last assigned ID for each project:

```yaml
projects:
  PRJ:
    last_root: 42
    subtasks:
      "5": 3 # PRJ-5-3 is last subtask of PRJ-5
```

## Workflow

### Regular Usage

```bash
# Add new tasks in Asana, then:
uvx aa-cli@latest update
```

### Adding New Projects

1. Edit `.aa.yml` to add the project
2. Run `uvx aa-cli@latest scan --project NEW`
3. Run `uvx aa-cli@latest update --project NEW`

### Handling Conflicts

If someone manually added IDs or cache is out of sync:

```bash
# Review the conflict
uvx aa-cli@latest scan

# If safe, update cache to match Asana
uvx aa-cli@latest scan --ignore-conflicts
```

## Troubleshooting

**"Config file not found"**

- Run `uvx aa-cli@latest init` first

**"Invalid token" or 401 errors**

- Generate new token at [Asana Developer Console](https://app.asana.com/0/developer-console)
- Update `.aa.yml`

**"Conflict detected"**

- Someone may have manually added IDs
- Review tasks in Asana
- Use `--ignore-conflicts` if safe

**Tasks not getting IDs**

- Check if tasks already have IDs (they're skipped)
- Make sure you're running `update`, not just `scan`
- Remove `--dry-run` flag

## Development

For contributors and developers:

### Setup

```bash
git clone https://github.com/umaxfun/asana-tools
cd asana-tools
uv sync
```

### Run Locally

```bash
uv run aa-cli --help
```

### Project Structure

```
aa/
├── cli.py              # Main CLI entry point
├── commands/           # Command implementations
├── core/               # Business logic
├── models/             # Data models
└── utils/              # Utilities
```

### Testing

```bash
uv run pytest
```

### Adding Dependencies

```bash
uv add <package-name>
```

### Version Management

To bump the version and release a new tag:

```bash
# Bump version (updates pyproject.toml and aa/__init__.py)
python scripts/bump_version.py [major|minor|patch]

# Push commits and create a git tag
python scripts/push_tag.py
```

The `push_tag.py` script will:

- Show git status to help you catch uncommitted changes
- Ask for confirmation before proceeding
- Push all commits to origin
- Create and push a version tag (e.g., `v0.4.3`)

## License

MIT

## Support

- [Open an issue](https://github.com/umaxfun/asana-tools/issues)
- Check existing issues for solutions
