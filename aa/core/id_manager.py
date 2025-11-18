"""ID management logic for task identifiers."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Regex pattern for extracting IDs: CODE-N or CODE-N-M-...
# Matches project code (2-5 uppercase letters) followed by dash and numbers with optional sub-levels
ID_PATTERN = r'^([A-Z]{2,5})-(\d+(?:-\d+)*)(?:\s|$)'


class IDManager:
    """Manages logic for assigning and tracking task IDs.
    
    This class handles:
    - Extracting existing IDs from task names
    - Checking if tasks have IDs
    - Generating new IDs for root tasks and subtasks
    - Managing ID counters through cache
    """
    
    def __init__(self, cache_data: Optional[dict] = None):
        """Initialize the ID Manager.
        
        Args:
            cache_data: Optional cache data structure with project counters
        """
        self.cache = cache_data or {}
        logger.debug("IDManager initialized")
    
    def extract_id(self, task_name: str, project_code: str) -> Optional[str]:
        """Extract ID from task name using regex.
        
        Extracts IDs in the format CODE-N or CODE-N-M-... from the beginning
        of the task name, where CODE matches the provided project_code.
        
        Args:
            task_name: The task name to extract ID from
            project_code: The expected project code (2-5 uppercase letters)
            
        Returns:
            The extracted ID (e.g., "PRJ-5", "PRJ-5-2") or None if no ID found
            
        Examples:
            >>> manager = IDManager()
            >>> manager.extract_id("PRJ-5 My task", "PRJ")
            'PRJ-5'
            >>> manager.extract_id("AB-5-2 Subtask", "AB")
            'AB-5-2'
            >>> manager.extract_id("PROJ-5-2-1 Nested", "PROJ")
            'PROJ-5-2-1'
            >>> manager.extract_id("My task", "PRJ")
            None
        """
        match = re.match(ID_PATTERN, task_name)
        if match and match.group(1) == project_code:
            extracted_id = f"{match.group(1)}-{match.group(2)}"
            logger.debug(f"Extracted ID '{extracted_id}' from task: {task_name}")
            return extracted_id
        
        logger.debug(f"No ID found in task: {task_name}")
        return None
    
    def has_id(self, task_name: str, project_code: str) -> bool:
        """Check if task name contains an ID.
        
        Args:
            task_name: The task name to check
            project_code: The expected project code
            
        Returns:
            True if task has an ID, False otherwise
            
        Examples:
            >>> manager = IDManager()
            >>> manager.has_id("PRJ-5 My task", "PRJ")
            True
            >>> manager.has_id("My task", "PRJ")
            False
        """
        return self.extract_id(task_name, project_code) is not None
    
    def generate_next_root_id(self, project_code: str) -> str:
        """Generate the next ID for a root task.
        
        Uses the last_root counter from cache to determine the next ID.
        If no cache exists for the project, starts from 1.
        
        Args:
            project_code: The project code
            
        Returns:
            The next root task ID (e.g., "PRJ-6")
            
        Examples:
            >>> manager = IDManager({'PRJ': {'last_root': 5}})
            >>> manager.generate_next_root_id('PRJ')
            'PRJ-6'
            >>> manager = IDManager({})
            >>> manager.generate_next_root_id('NEW')
            'NEW-1'
        """
        # Get project cache or initialize
        project_cache = self.cache.get(project_code, {})
        last_root = project_cache.get('last_root', 0)
        
        # Generate next ID
        next_id = last_root + 1
        next_id_str = f"{project_code}-{next_id}"
        
        logger.debug(f"Generated next root ID: {next_id_str} (previous: {last_root})")
        return next_id_str
    
    def generate_next_subtask_id(self, parent_id: str, project_code: str) -> str:
        """Generate the next ID for a subtask.
        
        Uses the parent task's counter from the subtasks section of cache.
        If no counter exists for the parent, starts from 1.
        
        Args:
            parent_id: The parent task's ID (e.g., "PRJ-5" or "PRJ-5-2")
            project_code: The project code
            
        Returns:
            The next subtask ID (e.g., "PRJ-5-3" or "PRJ-5-2-4")
            
        Examples:
            >>> manager = IDManager({'PRJ': {'subtasks': {'5': 2}}})
            >>> manager.generate_next_subtask_id('PRJ-5', 'PRJ')
            'PRJ-5-3'
            >>> manager = IDManager({'PRJ': {'subtasks': {'5-2': 3}}})
            >>> manager.generate_next_subtask_id('PRJ-5-2', 'PRJ')
            'PRJ-5-2-4'
            >>> manager = IDManager({})
            >>> manager.generate_next_subtask_id('PRJ-10', 'PRJ')
            'PRJ-10-1'
        """
        # Extract the numeric part of parent ID (remove project code prefix)
        # E.g., "PRJ-5" -> "5", "PRJ-5-2" -> "5-2"
        parent_numeric = parent_id.replace(f"{project_code}-", "", 1)
        
        # Get project cache
        project_cache = self.cache.get(project_code, {})
        subtasks_cache = project_cache.get('subtasks', {})
        
        # Get last subtask counter for this parent
        last_subtask = subtasks_cache.get(parent_numeric, 0)
        
        # Generate next ID
        next_subtask = last_subtask + 1
        next_id_str = f"{parent_id}-{next_subtask}"
        
        logger.debug(f"Generated next subtask ID: {next_id_str} (parent: {parent_id}, previous: {last_subtask})")
        return next_id_str
