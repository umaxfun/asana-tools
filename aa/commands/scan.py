"""Scan command for analyzing projects and updating cache."""

import asyncio
import logging
import signal
import sys
from typing import Optional

import click

from aa.core.asana_client import AsanaClient
from aa.core.id_manager import IDManager
from aa.models.config import Config
from aa.utils.cache_manager import load_cache, save_cache
from aa.utils.config_loader import load_config, ConfigurationError

logger = logging.getLogger(__name__)


class ScanError(Exception):
    """Raised when scan operation encounters an error."""
    pass


async def scan_project(
    project_code: str,
    project_id: str,
    asana_client: AsanaClient,
    id_manager: IDManager,
    ignore_conflicts: bool = False,
    silent: bool = False
) -> dict[str, any]:
    """Scan a single project and extract existing IDs.
    
    Args:
        project_code: The project code (e.g., "PRJ")
        project_id: The Asana project GID
        asana_client: Asana API client
        id_manager: ID manager with cache
        ignore_conflicts: If True, update cache to max values on conflict
        
    Returns:
        Dictionary with scan results
        
    Raises:
        ScanError: If conflicts detected and ignore_conflicts is False
    """
    if not silent:
        logger.info(f"Scanning project {project_code} (ID: {project_id})")
    
    # Get all tasks from project
    tasks = await asana_client.get_project_tasks(project_id)
    if not silent:
        logger.info(f"Found {len(tasks)} tasks in project {project_code}")
    
    # Extract existing IDs from task names
    existing_ids = []
    for task in tasks:
        task_name = task.get('name', '')
        task_id = id_manager.extract_id(task_name, project_code)
        if task_id:
            existing_ids.append(task_id)
            if not silent:
                logger.debug(f"Found existing ID: {task_id} in task '{task_name}'")
    
    if not silent:
        logger.info(f"Found {len(existing_ids)} existing IDs in project {project_code}")
    
    # Detect conflicts
    conflicts = id_manager.detect_conflicts(existing_ids, project_code)
    
    if conflicts:
        if ignore_conflicts:
            logger.warning(f"Conflicts detected but --ignore-conflicts flag set, updating cache")
            # Update cache to maximum found values
            max_root = id_manager.find_max_id(existing_ids, project_code)
            if project_code not in id_manager.cache_data.projects:
                from aa.models.cache import ProjectCache
                id_manager.cache_data.projects[project_code] = ProjectCache()
            
            id_manager.cache_data.projects[project_code].last_root = max_root
            logger.info(f"Updated {project_code} last_root to {max_root}")
            
            # Update subtask counters
            for task_id in existing_ids:
                # Extract numeric part
                numeric_part = task_id.replace(f"{project_code}-", "", 1)
                if '-' in numeric_part:
                    # This is a subtask
                    parts = numeric_part.rsplit('-', 1)
                    parent_numeric = parts[0]
                    subtask_number = int(parts[1])
                    
                    current_max = id_manager.cache_data.projects[project_code].subtasks.get(parent_numeric, 0)
                    if subtask_number > current_max:
                        id_manager.cache_data.projects[project_code].subtasks[parent_numeric] = subtask_number
                        logger.debug(f"Updated subtask counter for {project_code}-{parent_numeric} to {subtask_number}")
        else:
            # Raise error with all conflicts
            error_msg = f"Conflicts detected in project {project_code}:\n"
            for conflict in conflicts:
                error_msg += f"  - {conflict}\n"
            error_msg += "\nUse --ignore-conflicts flag to update cache and continue."
            raise ScanError(error_msg)
    
    # Update cache with maximum found IDs if no conflicts or conflicts ignored
    if not conflicts or ignore_conflicts:
        max_root = id_manager.find_max_id(existing_ids, project_code)
        if project_code not in id_manager.cache_data.projects:
            from aa.models.cache import ProjectCache
            id_manager.cache_data.projects[project_code] = ProjectCache()
        
        # Only update if we found IDs and they're higher than current cache
        if max_root > 0:
            current_last_root = id_manager.cache_data.projects[project_code].last_root
            if max_root > current_last_root:
                id_manager.cache_data.projects[project_code].last_root = max_root
                logger.info(f"Updated {project_code} last_root from {current_last_root} to {max_root}")
            else:
                logger.debug(f"Cache already up to date for {project_code} (last_root: {current_last_root})")
    
    return {
        'project_code': project_code,
        'total_tasks': len(tasks),
        'tasks_with_ids': len(existing_ids),
        'conflicts': conflicts
    }


async def scan_projects_async(
    config: Config,
    project_code: Optional[str],
    ignore_conflicts: bool,
    silent: bool = False
) -> None:
    """Async implementation of project scanning.
    
    Args:
        config: Configuration object
        project_code: Optional specific project to scan
        ignore_conflicts: Whether to ignore ID conflicts
        
    Raises:
        ScanError: If scan fails
    """
    # Load cache
    cache = load_cache()
    id_manager = IDManager(cache)
    
    # Setup signal handler to save cache on interruption
    interrupted = False
    
    def signal_handler(signum, frame):
        nonlocal interrupted
        interrupted = True
        logger.warning("\nReceived interrupt signal, saving cache...")
        try:
            save_cache(id_manager.cache_data)
            if not silent:
                click.echo("\n✓ Cache saved before exit")
        except Exception as e:
            logger.error(f"Failed to save cache on interrupt: {e}")
        raise KeyboardInterrupt()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create Asana client
    asana_client = AsanaClient(config.asana_token)
    
    try:
        # Determine which projects to scan
        if project_code:
            # Scan specific project
            project_config = next(
                (p for p in config.projects if p.code == project_code),
                None
            )
            if not project_config:
                raise ScanError(f"Project '{project_code}' not found in configuration")
            
            projects_to_scan = [project_config]
        else:
            # Scan all projects
            projects_to_scan = config.projects
        
        if not silent:
            logger.info(f"Scanning {len(projects_to_scan)} project(s)")
        
        # Scan each project
        results = []
        for project in projects_to_scan:
            try:
                result = await scan_project(
                    project.code,
                    project.asana_id,
                    asana_client,
                    id_manager,
                    ignore_conflicts,
                    silent
                )
                results.append(result)
            except ScanError:
                # Re-raise scan errors (conflicts, etc.)
                raise
            except Exception as e:
                logger.error(f"Error scanning project {project.code}: {e}")
                raise ScanError(f"Failed to scan project {project.code}: {e}")
        
        # Save updated cache
        save_cache(id_manager.cache_data)
        if not silent:
            logger.info("Cache updated successfully")
        
        # Print summary (skip in silent mode)
        if not silent:
            click.echo("\n=== Scan Summary ===")
            for result in results:
                click.echo(f"\nProject: {result['project_code']}")
                click.echo(f"  Total tasks: {result['total_tasks']}")
                click.echo(f"  Tasks with IDs: {result['tasks_with_ids']}")
                if result['conflicts']:
                    click.echo(f"  Conflicts: {len(result['conflicts'])} (resolved with --ignore-conflicts)")
            
            click.echo(f"\n✓ Cache saved to .aa.cache.yaml")
        
    finally:
        await asana_client.close()


@click.command()
@click.option('--config', default='.aa.yml', help='Path to config file')
@click.option('--project', help='Project code to scan (default: all)')
@click.option('-v', '--verbose', count=True, help='Increase verbosity (-v for INFO, -vv for DEBUG)')
@click.option('--ignore-conflicts', is_flag=True, help='Ignore ID conflicts and update cache')
def scan(config: str, project: Optional[str], verbose: int, ignore_conflicts: bool) -> None:
    """Scan projects and update cache with existing IDs.
    
    This command:
    - Loads configuration from .aa.yml
    - Fetches all tasks from specified project(s)
    - Extracts existing IDs from task names
    - Detects conflicts (IDs greater than cache, duplicates)
    - Updates cache with found IDs
    - Saves cache to .aa.cache.yaml
    
    Examples:
        aa scan                    # Scan all projects
        aa scan --project PRJ      # Scan specific project
        aa scan --ignore-conflicts # Ignore conflicts and update cache
        aa scan -v                 # Verbose output
        aa scan -vv                # Very verbose output with HTTP logs
    """
    # Setup logging based on verbosity (override CLI group setting)
    if verbose > 0:
        level = logging.INFO if verbose == 1 else logging.DEBUG
        logging.getLogger().setLevel(level)
        # Suppress noisy third-party loggers at INFO level
        if verbose == 1:
            logging.getLogger('httpx').setLevel(logging.WARNING)
            logging.getLogger('httpcore').setLevel(logging.WARNING)
            logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    try:
        # Load configuration
        config_obj = load_config(config)
        
        # Run async scan
        asyncio.run(scan_projects_async(config_obj, project, ignore_conflicts))
        
    except ConfigurationError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except ScanError as e:
        click.echo(f"Scan error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nScan interrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error during scan")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)
