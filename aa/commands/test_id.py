"""Test command for ID extraction functionality."""

import click
import logging

from aa.core.id_manager import IDManager

logger = logging.getLogger(__name__)


@click.command('test-id')
@click.argument('task_name')
@click.argument('project_code')
def test_id(task_name: str, project_code: str) -> None:
    """Test ID extraction from task name.
    
    This is a utility command for testing the ID extraction functionality.
    
    Args:
        task_name: The task name to extract ID from
        project_code: The project code to match
        
    Examples:
        aa test-id "PRJ-5 My task" PRJ
        aa test-id "AB-10-2 Subtask" AB
    """
    # Create ID manager (no cache needed for extraction)
    manager = IDManager()
    
    # Try to extract ID
    extracted_id = manager.extract_id(task_name, project_code)
    
    if extracted_id:
        click.echo(f"Found ID: {extracted_id}")
    else:
        click.echo(f"No ID found in task name")
