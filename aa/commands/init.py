"""Init command for creating configuration file."""

import logging
from pathlib import Path
import click
import yaml


logger = logging.getLogger(__name__)


CONFIG_TEMPLATE = {
    'asana_token': 'YOUR_ASANA_PERSONAL_ACCESS_TOKEN',
    'interactive': False,
    'projects': [
        {
            'code': 'PRJ',
            'asana_id': '1234567890123456'
        },
        {
            'code': 'TSK',
            'asana_id': '9876543210987654'
        }
    ]
}


@click.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize aa configuration file.
    
    Creates a .aa.yml configuration file with template values.
    """
    config_path = ctx.obj.get('config', '.aa.yml')
    config_file = Path(config_path)
    
    # Check if file already exists
    if config_file.exists():
        logger.warning(f"Configuration file {config_path} already exists. Aborting.")
        click.echo(f"⚠️  Configuration file {config_path} already exists.")
        click.echo("Please remove or rename the existing file before running init.")
        ctx.exit(1)
    
    # Create the config file
    try:
        with open(config_file, 'w') as f:
            yaml.dump(CONFIG_TEMPLATE, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Created configuration file: {config_path}")
        click.echo(f"✓ Created configuration file: {config_path}")
        click.echo("\nNext steps:")
        click.echo("1. Edit .aa.yml and add your Asana Personal Access Token")
        click.echo("2. Update project codes and Asana project IDs")
        click.echo("3. Run 'aa scan' to initialize the cache")
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}")
        click.echo(f"✗ Failed to create configuration file: {e}")
        ctx.exit(1)
