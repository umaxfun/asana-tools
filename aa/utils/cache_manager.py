"""Cache management utilities."""

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from aa.models.cache import CacheData, ProjectCache

logger = logging.getLogger(__name__)

DEFAULT_CACHE_FILE = ".aa.cache.yaml"


def load_cache(cache_path: str = DEFAULT_CACHE_FILE) -> CacheData:
    """Load cache data from YAML file.
    
    If the cache file doesn't exist, returns an empty cache structure.
    If the file exists but is invalid, raises an error.
    
    Args:
        cache_path: Path to cache file (default: .aa.cache.yaml)
        
    Returns:
        CacheData object with loaded cache information
        
    Raises:
        ValidationError: If cache file has invalid structure
        yaml.YAMLError: If cache file has invalid YAML syntax
    """
    cache_file = Path(cache_path)
    
    if not cache_file.exists():
        logger.info(f"Cache file not found at {cache_path}, starting with empty cache")
        return CacheData()
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            logger.info(f"Cache file {cache_path} is empty, starting with empty cache")
            return CacheData()
        
        cache = CacheData(**data)
        logger.info(f"Loaded cache from {cache_path}")
        logger.debug(f"Cache contains {len(cache.projects)} project(s)")
        return cache
        
    except ValidationError as e:
        logger.error(f"Invalid cache structure in {cache_path}: {e}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in cache file {cache_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading cache from {cache_path}: {e}")
        raise


def save_cache(cache: CacheData, cache_path: str = DEFAULT_CACHE_FILE) -> None:
    """Save cache data to YAML file.
    
    Converts the CacheData object to a dictionary and saves it as YAML.
    Creates the file if it doesn't exist.
    
    Args:
        cache: CacheData object to save
        cache_path: Path to cache file (default: .aa.cache.yaml)
        
    Raises:
        IOError: If unable to write to cache file
    """
    try:
        cache_file = Path(cache_path)
        
        # Convert Pydantic model to dict
        data = cache.model_dump()
        
        # Write to YAML file
        with open(cache_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        logger.info(f"Saved cache to {cache_path}")
        logger.debug(f"Cache contains {len(cache.projects)} project(s)")
        
    except Exception as e:
        logger.error(f"Error saving cache to {cache_path}: {e}")
        raise
