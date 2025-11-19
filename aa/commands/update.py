"""Update command for assigning IDs to tasks."""

import asyncio
import logging
import signal
import sys
from typing import Optional

import click

from aa.core.asana_client import AsanaClient
from aa.core.id_manager import IDManager
from aa.core.task_processor import TaskProcessor
from aa.models.config import Config
from aa.utils.cache_manager import load_cache, save_cache
from aa.utils.config_loader import load_config, ConfigurationError
from aa.commands.scan import scan_projects_async, ScanError

logger = logging.getLogger(__name__)


class UpdateError(Exception):
    """Raised when update operation encounters an error."""
    pass


async def update_projects_async(
    config: Config,
    project_code: Optional[str],
    dry_run: bool,
    ignore_conflicts: bool
) -> None:
    """Async implementation of project update.
    
    Args:
        config: Configuration object
        project_code: Optional specific project to update
        dry_run: If True, show changes without applying them
        ignore_conflicts: Whether to ignore ID conflicts during scan
        
    Raises:
        UpdateError: If update fails
    """
    # First, run scan to check for conflicts and update cache
    # In dry-run mode, run scan silently to avoid cluttering output
    if not dry_run:
        logger.info("Running scan to check for conflicts...")
    try:
        await scan_projects_async(config, project_code, ignore_conflicts, silent=dry_run)
    except ScanError as e:
        raise UpdateError(f"Scan failed: {e}")
    
    # Load cache (refreshed by scan)
    cache = load_cache()
    
    # In dry-run mode, work with a copy of cache so we can preview without affecting the real cache
    if dry_run:
        import copy
        cache = copy.deepcopy(cache)
    
    id_manager = IDManager(cache)
    
    # Setup signal handler to save cache on interruption
    interrupted = False
    
    def signal_handler(signum, frame):
        nonlocal interrupted
        interrupted = True
        logger.warning("\nReceived interrupt signal, saving cache...")
        if not dry_run:
            try:
                save_cache(id_manager.cache_data)
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
        # Determine which projects to update
        if project_code:
            # Update specific project
            project_config = next(
                (p for p in config.projects if p.code == project_code),
                None
            )
            if not project_config:
                raise UpdateError(f"Project '{project_code}' not found in configuration")
            
            projects_to_update = [project_config]
        else:
            # Update all projects
            projects_to_update = config.projects
        
        logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Updating {len(projects_to_update)} project(s)")
        
        if dry_run:
            click.echo("\n=== DRY-RUN MODE ===")
            click.echo("No changes will be made to Asana or cache\n")
        
        # Create task processor
        task_processor = TaskProcessor(asana_client, id_manager)
        
        # Process projects in parallel using asyncio.gather()
        logger.info(f"Processing {len(projects_to_update)} project(s) in parallel")
        
        async def process_single_project(project):
            """Process a single project and handle errors."""
            try:
                return await task_processor.process_project(
                    project.asana_id,
                    project.code,
                    dry_run=dry_run
                )
            except Exception as e:
                logger.error(f"Error updating project {project.code}: {e}")
                raise UpdateError(f"Failed to update project {project.code}: {e}")
        
        # Process all projects concurrently
        results = await asyncio.gather(
            *[process_single_project(project) for project in projects_to_update]
        )
        
        # Save updated cache (unless dry-run)
        if not dry_run:
            save_cache(id_manager.cache_data)
            logger.info("Cache updated successfully")
        
        # Print summary
        click.echo("\n=== Update Summary ===")
        for result in results:
            click.echo(f"\nProject: {result.project_code}")
            click.echo(f"  Total tasks processed: {result.total_processed}")
            click.echo(f"  Tasks updated: {len(result.updates)}")
            click.echo(f"  Tasks skipped (already have ID): {result.skipped}")
            
            if result.errors:
                click.echo(f"  Errors: {len(result.errors)}")
                for error in result.errors:
                    click.echo(f"    - {error}")
            
            # Show updates in dry-run mode
            if dry_run and result.updates:
                click.echo(f"\n  IDs that would be assigned:")
                for update in result.updates[:10]:  # Show first 10
                    click.echo(f"    {update.assigned_id}: {update.old_name}")
                if len(result.updates) > 10:
                    click.echo(f"    ... and {len(result.updates) - 10} more")
        
        if dry_run:
            click.echo(f"\n✓ Dry-run complete. No changes were made.")
            click.echo(f"  Run without --dry-run to apply these changes.")
        else:
            click.echo(f"\n✓ Tasks updated successfully")
            click.echo(f"✓ Cache saved to .aa.cache.yaml")
        
    finally:
        await asana_client.close()


@click.command()
@click.option('--config', default='.aa.yml', help='Path to config file')
@click.option('--project', help='Project code to update (default: all)')
@click.option('--dry-run', is_flag=True, help='Show changes without applying them')
@click.option('-v', '--verbose', count=True, help='Increase verbosity (-v for INFO, -vv for DEBUG)')
@click.option('--ignore-conflicts', is_flag=True, help='Ignore ID conflicts during scan')
def update(
    config: str,
    project: Optional[str],
    dry_run: bool,
    verbose: int,
    ignore_conflicts: bool
) -> None:
    """Assign IDs to tasks without them.
    
    This command:
    - Runs scan to check for conflicts and update cache
    - Loads configuration from .aa.yml
    - Processes all tasks in specified project(s)
    - Skips tasks that already have IDs
    - Assigns new IDs to tasks without them
    - Updates task names in Asana (unless --dry-run)
    - Updates and saves cache (unless --dry-run)
    
    Examples:
        aa update --dry-run        # Preview changes without applying
        aa update                  # Update all projects
        aa update --project PRJ    # Update specific project
        aa update --ignore-conflicts  # Ignore conflicts and continue
        aa update -v               # Verbose output
        aa update -vv              # Very verbose output with HTTP logs
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
        
        # Run async update
        asyncio.run(update_projects_async(config_obj, project, dry_run, ignore_conflicts))
        
    except ConfigurationError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except UpdateError as e:
        click.echo(f"Update error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nUpdate interrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error during update")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)
