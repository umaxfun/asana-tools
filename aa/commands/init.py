"""Init command for creating configuration file."""

import asyncio
import logging
import re
from pathlib import Path
import click
import yaml

from aa.core.asana_client import AsanaClient
from aa.core.id_manager import ID_PATTERN
from aa.models.config import Config, ProjectConfig


logger = logging.getLogger(__name__)


def create_template_config() -> Config:
    """Create a template configuration using Pydantic models."""
    return Config(
        asana_token="YOUR_ASANA_PERSONAL_ACCESS_TOKEN",
        interactive=False,
        projects=[
            ProjectConfig(code="PROJ", asana_id="1234567890123456"),
            ProjectConfig(code="TASK", asana_id="9876543210987654"),
        ],
    )


async def detect_project_code(client: AsanaClient, project_id: str) -> str | None:
    """Detect project code from existing tasks.

    Fetches a sample of tasks and checks if they have IDs matching the pattern.
    Raises click.ClickException if multiple different project codes are found.
    """
    try:
        # Fetch recent tasks (limit to 100 as requested)
        tasks = await client.get_project_tasks(project_id, limit=100)

        found_codes = set()

        for task in tasks:
            name = task["name"]
            match = re.match(ID_PATTERN, name)
            if match:
                found_codes.add(match.group(1))

        if len(found_codes) > 1:
            codes_str = ", ".join(sorted(found_codes))
            raise click.ClickException(
                f"Multiple project codes found in project {project_id}: {codes_str}. "
                "Please fix the task names or use 'aa reset' to clean up IDs."
            )

        if found_codes:
            return found_codes.pop()

    except click.ClickException:
        raise
    except Exception as e:
        logger.warning(f"Failed to detect code for project {project_id}: {e}")

    return None


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
            workspace_id = workspace["gid"]
            projects = await client.get_projects(workspace_id)
            all_projects.extend(projects)

        click.echo(f"✓ Found {len(all_projects)} project(s)")

        # If there are 100+ projects, skip scanning to avoid rate limiting
        if len(all_projects) >= 100:
            click.echo(f"⚠️  Workspace has {len(all_projects)} projects (limit reached)")
            click.echo("   Skipping automatic code detection to avoid API rate limits")
            click.echo(
                "   Keeping only first project as example - add your projects manually"
            )
            all_projects = all_projects[:1] if all_projects else []
            return all_projects

        # Detect codes for all projects in parallel (with rate limiting)
        click.echo("Scanning projects for existing codes...")

        # Limit concurrent requests to avoid rate limiting
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

        async def process_project(project):
            async with semaphore:
                code = await detect_project_code(client, project["gid"])
                if code:
                    project["detected_code"] = code
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
                return project

        # Process all projects concurrently (but limited by semaphore)
        tasks = [process_project(p) for p in all_projects]
        all_projects = await asyncio.gather(*tasks)

        # Count how many codes were detected
        detected_count = sum(1 for p in all_projects if "detected_code" in p)
        if detected_count > 0:
            click.echo(f"✓ Detected existing codes for {detected_count} project(s)")

        return all_projects

    finally:
        await client.close()


def write_config_with_comments(
    config_path: Path, token: str, projects: list[dict]
) -> None:
    """Write config file with project URL comments using Pydantic models.

    Args:
        config_path: Path to write the config file
        token: Asana token
        projects: List of projects from Asana API
    """
    # Create ProjectConfig instances with placeholder codes
    project_configs = [
        ProjectConfig(
            code=project.get("detected_code", "CODE"), asana_id=project["gid"]
        )
        for project in projects
    ]

    # Create Config instance
    config = Config(asana_token=token, interactive=False, projects=project_configs)

    # Write config with comments
    lines = []
    lines.append(f"asana_token: {repr(config.asana_token)}")
    lines.append(f"interactive: {str(config.interactive).lower()}")
    lines.append("projects:")

    for i, project in enumerate(projects):
        asana_id = project["gid"]
        project_name = project["name"]

        # Add comment with project name and URL
        lines.append(f"  # {project_name}")
        lines.append(f"  # https://app.asana.com/0/{asana_id}")

        detected_code = project.get("detected_code")
        if detected_code:
            lines.append(f"  - code: {detected_code}  # Detected from existing tasks")
        else:
            lines.append(
                f"  - code: REPLACE_ME  # TODO: Replace with 2-5 letter code (uppercase)"
            )

        lines.append(f"    asana_id: '{asana_id}'")

    config_path.write_text("\n".join(lines) + "\n")


@click.command()
@click.option(
    "-f", "--force", is_flag=True, help="Create template without interactive setup"
)
@click.option("--config", default=".aa.yml", help="Path to config file")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v for INFO, -vv for DEBUG)",
)
@click.pass_context
def init(ctx: click.Context, force: bool, config: str, verbose: int) -> None:
    """Initialize aa configuration file.

    By default, runs in interactive mode to prompt for your Asana token
    and fetch all your projects.
    Use --force to create a template file instead.
    """
    # Use command-level options if provided, otherwise fall back to context
    config_path = config if config != ".aa.yml" else ctx.obj.get("config", ".aa.yml")

    # Update logging if verbose flag is set at command level
    if verbose > 0:
        level = logging.INFO if verbose == 1 else logging.DEBUG
        logging.getLogger().setLevel(level)

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
            with open(config_file, "w") as f:
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

            try:
                token = click.prompt(
                    "Enter your Asana Personal Access Token", hide_input=True, type=str
                )
            except click.exceptions.Abort:
                click.echo()  # Print newline
                ctx.exit(1)

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
            click.echo(
                "   - Replace 'REPLACE_ME' with 2-5 letter codes (uppercase) for projects you want to use"
            )
            click.echo("   - Remove projects you don't need")
            click.echo("2. Run 'aa scan' to initialize the cache")
            click.echo("3. Run 'aa update' to assign IDs to tasks")

    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}", exc_info=True)
        click.echo(f"✗ Failed to create configuration file: {e}")
        ctx.exit(1)
