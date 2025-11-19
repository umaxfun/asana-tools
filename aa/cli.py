"""Main CLI interface for aa tool."""

import logging
import click

from aa.commands.init import init
from aa.commands.validate import validate
from aa.commands.test_id import test_id
from aa.commands.cache_info import cache_info
from aa.commands.list_tasks import list_tasks
from aa.commands.scan import scan
from aa.commands.update import update


def setup_logging(verbose: int = 0) -> None:
    """Configure logging for the application.
    
    Verbosity levels:
    - 0 (default): WARNING - only warnings, errors, and critical messages
    - 1 (-v): INFO - application logs
    - 2+ (-vv): DEBUG - detailed logs including HTTP requests
    """
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:  # verbose >= 2
        level = logging.DEBUG
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # For verbose=1 (INFO), suppress noisy third-party loggers
    if verbose == 1:
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)


@click.group()
@click.option('--config', default='.aa.yml', help='Path to config file')
@click.option('-v', '--verbose', count=True, help='Increase verbosity (-v for INFO, -vv for DEBUG)')
@click.pass_context
def cli(ctx: click.Context, config: str, verbose: int) -> None:
    """Asana Auto-ID tool for automatic task ID assignment."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose


# Register commands
cli.add_command(init)
cli.add_command(validate)
cli.add_command(test_id)
cli.add_command(cache_info)
cli.add_command(list_tasks)
cli.add_command(scan)
cli.add_command(update)


def main() -> None:
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
