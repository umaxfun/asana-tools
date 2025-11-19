# Product Overview

`aa` (Asana Auto-ID) is a command-line tool for automatic human-readable ID assignment to Asana tasks and subtasks.

## Purpose

The tool adds short, human-readable prefixes (like `PRJ-5`, `PRJ-5-1`) to task names in Asana, making them easier to reference in discussions, documentation, and team communication.

## Key Features

- **Automatic ID Assignment**: Assigns hierarchical IDs to tasks and subtasks
- **Conflict Detection**: Detects and handles ID conflicts between cache and Asana
- **Multi-Project Support**: Manages multiple Asana projects from a single configuration
- **Dry-Run Mode**: Preview changes before applying them
- **Async Processing**: Fast parallel processing of multiple projects
- **Interactive Setup**: Automatically fetches all your Asana projects during initialization

## Core Concepts

### ID Format
- Root tasks: `CODE-N` (e.g., `PRJ-5`)
- Subtasks: `CODE-N-M` (e.g., `PRJ-5-1`)
- Nested subtasks: `CODE-N-M-K` (e.g., `PRJ-5-1-2`)
- Unlimited nesting depth supported

### Configuration
- `.aa.yml` - Project configuration with Asana token and project mappings
- `.aa.cache.yaml` - Tracks last assigned IDs for each project (auto-managed)

### Main Commands
- `aa init` - Initialize configuration (interactive or template)
- `aa scan` - Scan projects and update cache with existing IDs
- `aa update` - Assign IDs to tasks without them

## Version
Current version: 0.1.0 (functional implementation complete)
