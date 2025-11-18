"""Init command for creating configuration file."""

import asyncio
import logging
from pathlib import Path
import click
import yaml

from aa.core.asana_client import AsanaClient
from aa.models.config import Config, ProjectConfig


logger = logging.getLogger(__name__)


def create_template_config() -> Config:
    """Create a template configuration using Pydantic models."""
    return Config(
        asana_token='YOUR_ASANA_PERSONAL_ACCESS_TOKEN',
        interactive=False,
        projects=[
            ProjectConfig(code='PROJ', asana_id='1234567890123456'),
            ProjectConfig(code='TASK', asana_id='9876543210987654')
        ]
    )


async def fetch_all_projects(token: str) -> list[dict]:
    """Fetch all projects from all workspaces.
    
    Args:
        token: Asana Personal Access Token
        
    Returns:
        List of projects with gid and name
    """
    client = AsanaClient(token)
    
    try:
        workspaces = await client.get_workspaces()
        click.echo(f"✓ Found {len(workspaces)} workspace(s)")
        
        all_projects = []
        for workspace in workspaces:
            workspace_id = workspace['gid']
            projects = await client.get_projects(workspace_id)
            all_projects.extend(projects)
        
        click.echo(f"✓ Found {len(all_projects)} project(s)")
        return all_projects
        
    finally:
        await client.close()


def write_config_with_comments(config_path: Path, token: str, projects: list[dict]) -> None:
    """Write config file with project URL comments using Pydantic models.
    
    Args:
        config_path: Path to write the config file
        token: Asana token
        projects: List of projects from Asana API
    """
    # Create ProjectConfig instances with placeholder codes
    project_configs = [
        ProjectConfig(code='CODE', asana_id=project['gid'])
        for project in projects
    ]
    
    # Create Config instance
    config = Config(
        asana_token=token,
        interactive=False,
        projects=project_configs
    )
    
    # Write config with comments
    lines = []
    lines.append(f"asana_token: {repr(config.asana_token)}")
    lines.append(f"interactive: {str(config.interactive).lower()}")
    lines.append("projects:")
    
    for i, project in enumerate(projects):
        asana_id = project['gid']
        project_name = project['name']
        
        # Add comment with project name and URL
        lines.append(f"  # {project_name}")
        lines.append(f"  # https://app.asana.com/0/{asana_id}")
        lines.append(f"  - code: CODE  # TODO: Replace with 2-5 letter code (uppercase)")
        lines.append(f"    asana_id: '{asana_id}'")
    
    config_path.write_text('\n'.join(lines) + '\n')


@click.command()
@click.option('-f', '--force', is_flag=True, help='Create template without interactive setup')
@click.option('--config', default='.aa.yml', help='Path to config file')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def init(ctx: click.Context, force: bool, config: str, debug: bool) -> None:
    """Initialize aa configuration file.
    
    By default, runs in interactive mode to prompt for your Asana token
    and fetch all your projects.
    Use --force to create a template file instead.
    """
    # Use command-level options if provided, otherwise fall back to context
    config_path = config if config != '.aa.yml' else ctx.obj.get('config', '.aa.yml')
    
    # Update logging if debug flag is set at command level
    if debug and not ctx.obj.get('debug', False):
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    config_file = Path(config_path)
    
    # Check if file already exists
    if config_file.exists():
        logger.warning(f"Configuration file {config_path} already exists. Aborting.")
        click.echo(f"⚠️  Configuration file {config_path} already exists.")
        click.echo("Please remove or rename the existing file before running init.")
        ctx.exit(1)
    
    try:
        if force:
            # Force mode: create template using Pydantic model
            template_config = create_template_config()
            
            # Convert to dict and write as YAML
            config_dict = template_config.model_dump()
            with open(config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Created template configuration file: {config_path}")
            click.echo(f"✓ Created template configuration file: {config_path}")
            click.echo("\nNext steps:")
            click.echo("1. Edit .aa.yml and add your Asana Personal Access Token")
            click.echo("2. Update project codes and Asana project IDs")
            click.echo("3. Run 'aa scan' to initialize the cache")
        else:
            # Interactive mode (default): prompt for token and fetch projects
            click.echo("🚀 Interactive initialization\n")
            
            token = click.prompt(
                "Enter your Asana Personal Access Token",
                hide_input=True,
                type=str
            )
            
            if not token or not token.strip():
                raise click.ClickException("Token cannot be empty")
            
            token = token.strip()
            
            # Fetch all projects from Asana
            click.echo("\n📡 Connecting to Asana...")
            projects = asyncio.run(fetch_all_projects(token))
            
            # Write config with comments
            write_config_with_comments(config_file, token, projects)
            
            logger.info(f"Created configuration file: {config_path}")
            click.echo(f"\n✓ Configuration saved to: {config_path}")
            click.echo(f"✓ Added {len(projects)} projects with URL comments")
            click.echo("\nNext steps:")
            click.echo("1. Edit .aa.yml to:")
            click.echo("   - Replace 'CODE' with 2-5 letter codes (uppercase) for projects you want to use")
            click.echo("   - Remove projects you don't need")
            click.echo("2. Run 'aa scan' to initialize the cache")
            click.echo("3. Run 'aa update' to assign IDs to tasks")
            
    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}", exc_info=True)
        click.echo(f"✗ Failed to create configuration file: {e}")
        ctx.exit(1)
