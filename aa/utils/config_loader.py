"""Configuration loading and validation utilities."""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from aa.models.config import Config

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


def load_config(config_path: str = '.aa.yml') -> Config:
    """Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file (default: .aa.yml)
        
    Returns:
        Validated Config object
        
    Raises:
        ConfigurationError: If file not found, invalid YAML, or validation fails
    """
    path = Path(config_path)
    
    # Check if file exists
    if not path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}\n"
            f"Run 'aa init' to create a configuration file."
        )
    
    # Load YAML
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Invalid YAML in configuration file: {config_path}\n"
            f"Error: {e}"
        )
    except Exception as e:
        raise ConfigurationError(
            f"Failed to read configuration file: {config_path}\n"
            f"Error: {e}"
        )
    
    # Validate with Pydantic
    try:
        config = Config(**data)
        logger.debug(f"Successfully loaded config from {config_path}")
        logger.debug(f"Found {len(config.projects)} project(s)")
        return config
    except ValidationError as e:
        # Format validation errors nicely
        error_messages = []
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_messages.append(f"  - {field}: {message}")
        
        raise ConfigurationError(
            f"Configuration validation failed: {config_path}\n"
            + '\n'.join(error_messages)
        )
    except Exception as e:
        raise ConfigurationError(
            f"Unexpected error validating configuration: {config_path}\n"
            f"Error: {e}"
        )
