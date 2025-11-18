"""Main CLI interface for aa tool."""

import logging
import click

from aa.commands.init import init
from aa.commands.validate import validate
from aa.commands.test_id import test_id


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.group()
@click.option('--config', default='.aa.yml', help='Path to config file')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx: click.Context, config: str, debug: bool) -> None:
    """Asana Auto-ID tool for automatic task ID assignment."""
    setup_logging(debug)
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['debug'] = debug


# Register commands
cli.add_command(init)
cli.add_command(validate)
cli.add_command(test_id)


def main() -> None:
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
