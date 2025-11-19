"""Command to list tasks from an Asana project."""

import asyncio
import logging

import click

from aa.core.asana_client import AsanaClient
from aa.utils.config_loader import load_config

logger = logging.getLogger(__name__)


@click.command(name='list-tasks')
@click.argument('project_id')
@click.option(
    '--config',
    default='.aa.yml',
    help='Path to config file',
    type=click.Path(exists=True)
)
@click.option(
    '--debug',
    is_flag=True,
    help='Enable debug logging'
)
def list_tasks(project_id: str, config: str, debug: bool) -> None:
    """List all tasks from an Asana project.
    
    PROJECT_ID: The Asana project GID to list tasks from
    
    This is a test command to verify the Asana API client is working correctly.
    It fetches all tasks from the specified project and displays them with their
    creation dates and subtask information.
    """
    # Setup logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load config to get the token
        cfg = load_config(config)
        
        # Run async operation
        asyncio.run(_list_tasks_async(project_id, cfg.asana_token))
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.error(f"Error in list-tasks command: {e}", exc_info=True)
        raise click.Abort()


async def _list_tasks_async(project_id: str, token: str) -> None:
    """Async implementation of list-tasks command.
    
    Args:
        project_id: The Asana project GID
        token: Asana Personal Access Token
    """
    client = AsanaClient(token)
    
    try:
        click.echo(f"📋 Fetching tasks from project {project_id}...")
        click.echo()
        
        # Get all tasks
        tasks = await client.get_project_tasks(project_id)
        
        if not tasks:
            click.echo("No tasks found in this project.")
            return
        
        click.echo(f"Found {len(tasks)} tasks:")
        click.echo("─" * 80)
        
        # Display each task
        for i, task in enumerate(tasks, 1):
            task_gid = task.get('gid', 'N/A')
            task_name = task.get('name', 'Unnamed')
            created_at = task.get('created_at', 'N/A')
            parent = task.get('parent')
            num_subtasks = task.get('num_subtasks', 0)
            
            # Format output
            click.echo(f"{i}. {task_name}")
            click.echo(f"   GID: {task_gid}")
            click.echo(f"   Created: {created_at}")
            
            if parent:
                parent_gid = parent.get('gid', 'N/A')
                click.echo(f"   Parent: {parent_gid}")
            
            # Show subtasks count if present
            if num_subtasks > 0:
                click.echo(f"   Subtasks: {num_subtasks}")
            
            click.echo()
        
        click.echo("─" * 80)
        click.echo(f"✅ Total: {len(tasks)} tasks")
        
    finally:
        await client.close()
