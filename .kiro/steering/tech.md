# Technology Stack

## Language & Version
- Python 3.12+ (required)
- Version managed via `.python-version` file
- Async/await pattern used throughout

## Build System
- Uses `pyproject.toml` for project configuration (PEP 621 standard)
- Package name: `asana-tools`
- **Package manager: UV only** - no pip, no manual virtualenv activation
- Console command registered as `aa` via `[project.scripts]`

## Core Dependencies

### Production
- **click** (>=8.1.0) - CLI framework with command groups and options
- **httpx** (>=0.27.0) - Async HTTP client for Asana API
- **pydantic** (>=2.0.0) - Data validation and settings management
- **pyyaml** (>=6.0.0) - YAML parsing for config and cache files

### Development
- **pytest** (>=8.0.0) - Testing framework
- **pytest-asyncio** (>=0.23.0) - Async test support
- **hypothesis** (>=6.0.0) - Property-based testing library

## Common Commands

```bash
# Run the console command (after uv sync)
uv run aa

# Install/sync dependencies and scripts
uv sync

# Add new dependencies
uv add <package-name>

# Add dev dependencies
uv add --dev <package-name>

# Run any Python command
uv run python <script.py>

# Run tests
uv run pytest

# Build for publishing
uv build
```

## Key Technical Patterns

### Async/Await
All I/O operations (HTTP requests, file operations) use async/await:
```python
async def get_project_tasks(self, project_id: str) -> list[dict]:
    response = await self.client.get(f"/projects/{project_id}/tasks")
    return response.json()
```

### Pydantic Validation
All data structures validated with Pydantic models:
```python
class ProjectConfig(BaseModel):
    code: str = Field(..., min_length=2, max_length=5, pattern="^[A-Z]{2,5}$")
    asana_id: str = Field(..., min_length=1)
```

### Click CLI Framework
Commands organized as Click command groups:
```python
@click.group()
@click.option('--config', default='.aa.yml')
@click.option('-v', '--verbose', count=True)
def cli(config: str, verbose: int):
    """Asana Auto-ID tool"""
```

### Error Handling
- Custom exception classes for different error types
- Retry logic with exponential backoff for API requests
- Graceful handling of rate limits (429 responses)

## API Integration

### Asana API
- Base URL: `https://app.asana.com/api/1.0`
- Authentication: Bearer token (Personal Access Token)
- Rate limit: 1500 requests/minute
- Automatic retry on 429 with `Retry-After` header

### HTTP Client Configuration
```python
httpx.AsyncClient(
    base_url="https://app.asana.com/api/1.0",
    headers={"Authorization": f"Bearer {token}"},
    timeout=30.0
)
```

## File Formats

### Configuration (`.aa.yml`)
- YAML format
- Pydantic validation on load
- Contains: token, projects list with codes and IDs

### Cache (`.aa.cache.yaml`)
- YAML format
- Tracks last assigned IDs per project
- Structure: `projects[code].last_root` and `projects[code].subtasks[parent_id]`

## Dependencies Management
All dependencies managed through UV. Add new dependencies using `uv add` command, which automatically updates `pyproject.toml`.

Never use pip directly - always use `uv add` or `uv remove`.
