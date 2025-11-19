"""Command to display cache information."""

import logging
from pathlib import Path

import click
import yaml

from aa.utils.cache_manager import DEFAULT_CACHE_FILE, load_cache

logger = logging.getLogger(__name__)


@click.command(name='cache-info')
@click.option(
    '--cache',
    default=DEFAULT_CACHE_FILE,
    help='Path to cache file',
    type=click.Path()
)
def cache_info(cache: str) -> None:
    """Display cache information.
    
    Shows the contents of the .aa.cache.yaml file in a readable format.
    Displays last assigned IDs for root tasks and subtasks for each project.
    """
    cache_file = Path(cache)
    
    if not cache_file.exists():
        click.echo(f"❌ Cache file not found: {cache}")
        click.echo("Run 'aa scan' to create the cache.")
        return
    
    try:
        # Load and validate cache
        cache_data = load_cache(cache)
        
        click.echo(f"📦 Cache file: {cache}")
        click.echo()
        
        if not cache_data.projects:
            click.echo("Cache is empty (no projects scanned yet)")
            return
        
        # Display cache information for each project
        for project_code, project_cache in cache_data.projects.items():
            click.echo(f"Project: {project_code}")
            click.echo(f"  Last root ID: {project_code}-{project_cache.last_root}")
            
            if project_cache.subtasks:
                click.echo(f"  Subtasks:")
                for parent_id, last_subtask in sorted(project_cache.subtasks.items()):
                    full_id = f"{project_code}-{parent_id}-{last_subtask}"
                    click.echo(f"    {project_code}-{parent_id} → {full_id}")
            else:
                click.echo(f"  Subtasks: (none)")
            
            click.echo()
        
        # Also show raw YAML for reference
        click.echo("Raw cache content:")
        click.echo("─" * 50)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            click.echo(content)
        
    except Exception as e:
        click.echo(f"❌ Error reading cache: {e}", err=True)
        logger.error(f"Error in cache-info command: {e}", exc_info=True)
        raise click.Abort()
