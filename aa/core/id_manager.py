"""ID management logic for task identifiers."""

import logging
import re
from typing import Optional, Union

from aa.models.cache import CacheData, ProjectCache

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
    
    def __init__(self, cache_data: Optional[Union[CacheData, dict]] = None):
        """Initialize the ID Manager.
        
        Args:
            cache_data: Optional CacheData object or dict with project counters
        """
        if isinstance(cache_data, CacheData):
            self.cache_data = cache_data
        elif isinstance(cache_data, dict):
            # For backward compatibility with dict-based cache
            self.cache_data = CacheData(projects={
                code: ProjectCache(**data) if isinstance(data, dict) else data
                for code, data in cache_data.items()
            })
        else:
            self.cache_data = CacheData()
        
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
            >>> from aa.models.cache import CacheData, ProjectCache
            >>> cache = CacheData(projects={'PRJ': ProjectCache(last_root=5)})
            >>> manager = IDManager(cache)
            >>> manager.generate_next_root_id('PRJ')
            'PRJ-6'
            >>> manager = IDManager()
            >>> manager.generate_next_root_id('NEW')
            'NEW-1'
        """
        # Get project cache or initialize
        if project_code not in self.cache_data.projects:
            self.cache_data.projects[project_code] = ProjectCache()
        
        project_cache = self.cache_data.projects[project_code]
        last_root = project_cache.last_root
        
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
            >>> from aa.models.cache import CacheData, ProjectCache
            >>> cache = CacheData(projects={'PRJ': ProjectCache(subtasks={'5': 2})})
            >>> manager = IDManager(cache)
            >>> manager.generate_next_subtask_id('PRJ-5', 'PRJ')
            'PRJ-5-3'
            >>> cache2 = CacheData(projects={'PRJ': ProjectCache(subtasks={'5-2': 3})})
            >>> manager2 = IDManager(cache2)
            >>> manager2.generate_next_subtask_id('PRJ-5-2', 'PRJ')
            'PRJ-5-2-4'
            >>> manager3 = IDManager()
            >>> manager3.generate_next_subtask_id('PRJ-10', 'PRJ')
            'PRJ-10-1'
        """
        # Extract the numeric part of parent ID (remove project code prefix)
        # E.g., "PRJ-5" -> "5", "PRJ-5-2" -> "5-2"
        parent_numeric = parent_id.replace(f"{project_code}-", "", 1)
        
        # Get project cache or initialize
        if project_code not in self.cache_data.projects:
            self.cache_data.projects[project_code] = ProjectCache()
        
        project_cache = self.cache_data.projects[project_code]
        
        # Get last subtask counter for this parent
        last_subtask = project_cache.subtasks.get(parent_numeric, 0)
        
        # Generate next ID
        next_subtask = last_subtask + 1
        next_id_str = f"{parent_id}-{next_subtask}"
        
        logger.debug(f"Generated next subtask ID: {next_id_str} (parent: {parent_id}, previous: {last_subtask})")
        return next_id_str
    
    def find_max_id(self, existing_ids: list[str], project_code: str) -> int:
        """Find the maximum root task ID number from a list of existing IDs.
        
        Analyzes a list of task IDs and returns the highest root task number.
        Only considers root task IDs (CODE-N format), ignoring subtasks.
        Returns 0 if the list is empty or contains no valid root IDs.
        
        Args:
            existing_ids: List of task IDs (e.g., ["PRJ-5", "PRJ-12", "PRJ-5-2"])
            project_code: The project code to filter by
            
        Returns:
            The maximum root task number, or 0 if none found
            
        Examples:
            >>> manager = IDManager()
            >>> manager.find_max_id(["PRJ-5", "PRJ-12", "PRJ-5-2"], "PRJ")
            12
            >>> manager.find_max_id(["PRJ-3", "PRJ-1"], "PRJ")
            3
            >>> manager.find_max_id([], "PRJ")
            0
            >>> manager.find_max_id(["PRJ-5-1", "PRJ-5-2"], "PRJ")
            0
        """
        if not existing_ids:
            logger.debug("No existing IDs provided, returning 0")
            return 0
        
        max_id = 0
        root_pattern = re.compile(rf'^{re.escape(project_code)}-(\d+)$')
        
        for task_id in existing_ids:
            match = root_pattern.match(task_id)
            if match:
                id_number = int(match.group(1))
                if id_number > max_id:
                    max_id = id_number
                    logger.debug(f"Found new max root ID: {id_number}")
        
        logger.debug(f"Maximum root ID for {project_code}: {max_id}")
        return max_id
    
    def detect_conflicts(self, existing_ids: list[str], project_code: str) -> list[str]:
        """Detect conflicts between cache and existing IDs in Asana.
        
        A conflict occurs when:
        1. An existing root task ID is greater than last_root in cache
        2. Duplicate IDs exist in the task list
        
        Args:
            existing_ids: List of task IDs found in Asana
            project_code: The project code to check
            
        Returns:
            List of conflict messages (empty if no conflicts)
            
        Examples:
            >>> from aa.models.cache import CacheData, ProjectCache
            >>> cache = CacheData(projects={'PRJ': ProjectCache(last_root=5)})
            >>> manager = IDManager(cache)
            >>> manager.detect_conflicts(['PRJ-3', 'PRJ-10'], 'PRJ')
            ['Root task ID PRJ-10 is greater than cached last_root (5)']
            >>> manager.detect_conflicts(['PRJ-3', 'PRJ-3'], 'PRJ')
            ['Duplicate ID found: PRJ-3']
        """
        conflicts = []
        
        # Get project cache
        project_cache = self.cache_data.projects.get(project_code)
        if not project_cache:
            # No cache exists, no conflicts possible
            logger.debug(f"No cache for project {project_code}, no conflicts")
            return conflicts
        
        # Check for duplicate IDs
        seen_ids = set()
        for task_id in existing_ids:
            if task_id in seen_ids:
                conflict_msg = f"Duplicate ID found: {task_id}"
                conflicts.append(conflict_msg)
                logger.warning(conflict_msg)
            seen_ids.add(task_id)
        
        # Check for root task IDs greater than cached last_root
        root_pattern = re.compile(rf'^{re.escape(project_code)}-(\d+)$')
        for task_id in existing_ids:
            match = root_pattern.match(task_id)
            if match:
                id_number = int(match.group(1))
                if id_number > project_cache.last_root:
                    conflict_msg = f"Root task ID {task_id} is greater than cached last_root ({project_cache.last_root})"
                    conflicts.append(conflict_msg)
                    logger.warning(conflict_msg)
        
        if conflicts:
            logger.warning(f"Found {len(conflicts)} conflict(s) for project {project_code}")
        else:
            logger.debug(f"No conflicts detected for project {project_code}")
        
        return conflicts
    
    def update_cache_for_id(self, task_id: str, project_code: str) -> None:
        """Update cache after assigning an ID to a task.
        
        Updates the appropriate counter (last_root or subtasks) based on the ID format.
        
        Args:
            task_id: The ID that was assigned (e.g., "PRJ-6" or "PRJ-5-3")
            project_code: The project code
            
        Examples:
            >>> from aa.models.cache import CacheData, ProjectCache
            >>> cache = CacheData(projects={'PRJ': ProjectCache(last_root=5)})
            >>> manager = IDManager(cache)
            >>> manager.update_cache_for_id('PRJ-6', 'PRJ')
            >>> manager.cache_data.projects['PRJ'].last_root
            6
            >>> manager.update_cache_for_id('PRJ-6-1', 'PRJ')
            >>> manager.cache_data.projects['PRJ'].subtasks['6']
            1
        """
        # Ensure project cache exists
        if project_code not in self.cache_data.projects:
            self.cache_data.projects[project_code] = ProjectCache()
        
        project_cache = self.cache_data.projects[project_code]
        
        # Extract numeric part (remove project code prefix)
        numeric_part = task_id.replace(f"{project_code}-", "", 1)
        
        # Check if this is a root task (no dashes in numeric part) or subtask
        if '-' not in numeric_part:
            # Root task: update last_root
            root_number = int(numeric_part)
            project_cache.last_root = root_number
            logger.debug(f"Updated last_root for {project_code} to {root_number}")
        else:
            # Subtask: update subtasks counter
            # Split to get parent and subtask number
            parts = numeric_part.rsplit('-', 1)
            parent_numeric = parts[0]
            subtask_number = int(parts[1])
            project_cache.subtasks[parent_numeric] = subtask_number
            logger.debug(f"Updated subtask counter for {project_code}-{parent_numeric} to {subtask_number}")
