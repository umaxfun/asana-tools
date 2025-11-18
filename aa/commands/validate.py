"""Validate command for checking configuration."""

import logging
import sys

import click

from aa.utils.config_loader import load_config, ConfigurationError

logger = logging.getLogger(__name__)


@click.command()
@click.option('--config', default='.aa.yml', help='Path to config file')
def validate(config: str) -> None:
    """Validate configuration file.
    
    Checks if the configuration file exists, is valid YAML,
    and passes all Pydantic validation rules.
    """
    try:
        cfg = load_config(config)
        
        # Print success message with details
        click.echo(click.style('✓ Configuration is valid', fg='green', bold=True))
        click.echo(f'\nConfiguration file: {config}')
        click.echo(f'Projects configured: {len(cfg.projects)}')
        
        for project in cfg.projects:
            click.echo(f'  - {project.code}: {project.asana_id}')
        
        sys.exit(0)
        
    except ConfigurationError as e:
        click.echo(click.style('✗ Configuration validation failed', fg='red', bold=True))
        click.echo(f'\n{e}')
        sys.exit(1)
    except Exception as e:
        click.echo(click.style('✗ Unexpected error', fg='red', bold=True))
        click.echo(f'\n{e}')
        logger.exception("Unexpected error during validation")
        sys.exit(1)
