"""Reset command for removing IDs from tasks."""

import asyncio
import logging
import re
import sys
import click

from aa.core.asana_client import AsanaClient
from aa.core.id_manager import ID_PATTERN
from aa.utils.config_loader import load_config, ConfigurationError

logger = logging.getLogger(__name__)


async def reset_project(
    project_id: str,
    token: str,
    force: bool,
    dry_run: bool
) -> None:
    """Reset project by removing IDs from all tasks.
    
    Args:
        project_id: Asana Project GID
        token: Asana Personal Access Token
        force: Skip confirmation
        dry_run: Show changes without applying
    """
    client = AsanaClient(token)
    
    try:
        click.echo(f"Fetching tasks for project {project_id}...")
        tasks = await client.get_project_tasks(project_id)
        
        tasks_to_update = []
        
        for task in tasks:
            name = task['name']
            match = re.match(ID_PATTERN, name)
            if match:
                # Original name is the part after the ID
                # ID_PATTERN matches "CODE-123 " or "CODE-123" at start
                # We need to strip the ID and any following whitespace
                
                # Get the full match string
                id_str = match.group(0)
                new_name = name[len(id_str):].strip()
                
                # If name becomes empty (was just ID), keep it empty? 
                # Or maybe we shouldn't touch it if it's just ID?
                # Assuming we just strip the ID prefix.
                
                tasks_to_update.append({
                    'gid': task['gid'],
                    'old_name': name,
                    'new_name': new_name,
                    'id_removed': match.group(1) + '-' + match.group(2)
                })
        
        if not tasks_to_update:
            click.echo("✓ No tasks with IDs found.")
            return

        # Preview changes
        click.echo(f"\nFound {len(tasks_to_update)} tasks to reset:")
        for item in tasks_to_update:
            click.echo(f"  - {item['old_name']} -> {item['new_name']}")
            
        if dry_run:
            click.echo("\n[DRY RUN] No changes made.")
            return
            
        if not force:
            click.confirm(
                f"\nAre you sure you want to remove IDs from these {len(tasks_to_update)} tasks?",
                abort=True
            )
            
        click.echo("\nRemoving IDs...")
        
        # Process updates concurrently
        async def update_task(item):
            try:
                await client.update_task_name(item['gid'], item['new_name'])
                return True
            except Exception as e:
                logger.error(f"Failed to update task {item['gid']}: {e}")
                return False
                
        results = await asyncio.gather(*[update_task(item) for item in tasks_to_update])
        success_count = sum(1 for r in results if r)
        
        click.echo(f"✓ Successfully reset {success_count}/{len(tasks_to_update)} tasks.")
        
    finally:
        await client.close()


@click.command()
@click.option('--project-id', required=True, help='Asana Project GID to reset')
@click.option('--config', default='.aa.yml', help='Path to config file (for token)')
@click.option('--force', is_flag=True, help='Skip confirmation')
@click.option('--dry-run', is_flag=True, help='Show changes without applying')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def reset(project_id: str, config: str, force: bool, dry_run: bool, debug: bool) -> None:
    """Remove IDs from all tasks in a project.
    
    Use this command to clean up a project that has incorrect or mixed IDs.
    It will strip any text matching the ID pattern (CODE-123) from the start of task names.
    
    Requires a configuration file to get the Asana token.
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        # Load config just to get the token
        # We don't strictly need valid project config, just the token
        try:
            config_obj = load_config(config)
            token = config_obj.asana_token
        except Exception:
            # Fallback: try to read token from env or prompt?
            # For now, stick to config file as primary source
            click.echo("Could not load token from config file.")
            token = click.prompt("Enter your Asana Personal Access Token", hide_input=True)
            
        asyncio.run(reset_project(project_id, token, force, dry_run))
        
    except click.Abort:
        click.echo("\nAborted.")
    except Exception as e:
        logger.error(f"Reset failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
