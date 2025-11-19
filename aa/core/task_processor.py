"""Task processor for handling task hierarchies and ID assignment."""

import logging
from typing import Optional

from aa.core.asana_client import AsanaClient
from aa.core.id_manager import IDManager
from aa.models.task import TaskUpdate

logger = logging.getLogger(__name__)


class ProcessingResult:
    """Result of processing a project."""
    
    def __init__(self, project_code: str):
        self.project_code = project_code
        self.updates: list[TaskUpdate] = []
        self.skipped: int = 0
        self.errors: list[str] = []
    
    def add_update(self, update: TaskUpdate) -> None:
        """Add a task update to the result."""
        self.updates.append(update)
    
    def add_skip(self) -> None:
        """Increment skipped task counter."""
        self.skipped += 1
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
    
    @property
    def total_processed(self) -> int:
        """Total number of tasks processed."""
        return len(self.updates) + self.skipped


class TaskProcessor:
    """Processes tasks and their hierarchies for ID assignment."""
    
    def __init__(self, asana_client: AsanaClient, id_manager: IDManager):
        """Initialize the task processor.
        
        Args:
            asana_client: Asana API client for fetching and updating tasks
            id_manager: ID manager for generating and tracking IDs
        """
        self.asana = asana_client
        self.id_manager = id_manager
    
    async def process_project(
        self,
        project_id: str,
        project_code: str,
        dry_run: bool = False
    ) -> ProcessingResult:
        """Process all tasks in a project.
        
        Args:
            project_id: Asana project GID
            project_code: Project code (e.g., "PRJ")
            dry_run: If True, don't actually update tasks or cache
            
        Returns:
            ProcessingResult with details of what was processed
        """
        logger.info(f"Processing project {project_code} (ID: {project_id})")
        result = ProcessingResult(project_code)
        
        # Get all tasks in the project
        tasks = await self.asana.get_project_tasks(project_id)
        logger.info(f"Found {len(tasks)} tasks in project {project_code}")
        
        # Process each root task (tasks without parents)
        for task in tasks:
            # Skip tasks that have a parent (they'll be processed as subtasks)
            if task.get('parent'):
                continue
            
            # Process this task and its subtasks recursively
            task_updates = await self.process_task_hierarchy(
                task,
                project_code,
                parent_id=None,
                dry_run=dry_run
            )
            
            for update in task_updates:
                result.add_update(update)
        
        logger.info(
            f"Processed {result.total_processed} tasks in {project_code}: "
            f"{len(result.updates)} updated, {result.skipped} skipped"
        )
        
        return result
    
    async def process_task_hierarchy(
        self,
        task: dict,
        project_code: str,
        parent_id: Optional[str] = None,
        dry_run: bool = False
    ) -> list[TaskUpdate]:
        """Recursively process a task and its subtasks.
        
        Args:
            task: Task dictionary from Asana API
            project_code: Project code (e.g., "PRJ")
            parent_id: Parent task's ID if this is a subtask (e.g., "PRJ-5")
            dry_run: If True, don't actually update tasks or cache
            
        Returns:
            List of TaskUpdate objects for all processed tasks
        """
        updates = []
        task_gid = task['gid']
        task_name = task['name']
        
        # Check if task already has an ID
        if self.id_manager.has_id(task_name, project_code):
            logger.debug(f"Task '{task_name}' already has ID, skipping")
            
            # Extract the existing ID to use as parent for subtasks
            existing_id = self.id_manager.extract_id(task_name, project_code)
            
            # Still process subtasks
            if task.get('num_subtasks', 0) > 0:
                subtasks = await self.asana.get_task_subtasks(task_gid)
                for subtask in subtasks:
                    subtask_updates = await self.process_task_hierarchy(
                        subtask,
                        project_code,
                        parent_id=existing_id,
                        dry_run=dry_run
                    )
                    updates.extend(subtask_updates)
            
            return updates
        
        # Generate new ID
        if parent_id:
            # This is a subtask
            new_id = self.id_manager.generate_next_subtask_id(parent_id, project_code)
        else:
            # This is a root task
            new_id = self.id_manager.generate_next_root_id(project_code)
        
        # Create new task name with ID
        new_name = f"{new_id} {task_name}"
        
        # Create update record
        update = TaskUpdate(
            task_id=task_gid,
            old_name=task_name,
            new_name=new_name,
            assigned_id=new_id
        )
        updates.append(update)
        
        logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Assigning ID {new_id} to task: {task_name}")
        
        # Update cache to track ID assignment (even in dry-run for correct preview)
        self.id_manager.update_cache_for_id(new_id, project_code)
        
        # Update task in Asana (unless dry-run)
        if not dry_run:
            try:
                await self.asana.update_task_name(task_gid, new_name)
                logger.debug(f"Successfully updated task {task_gid}")
            except Exception as e:
                logger.error(f"Failed to update task {task_gid}: {e}")
                raise
        
        # Process subtasks recursively
        if task.get('num_subtasks', 0) > 0:
            subtasks = await self.asana.get_task_subtasks(task_gid)
            for subtask in subtasks:
                subtask_updates = await self.process_task_hierarchy(
                    subtask,
                    project_code,
                    parent_id=new_id,
                    dry_run=dry_run
                )
                updates.extend(subtask_updates)
        
        return updates
