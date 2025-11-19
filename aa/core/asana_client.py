"""Asana API client for async operations."""

import asyncio
import logging
from typing import Any
import httpx


logger = logging.getLogger(__name__)


class AsanaClient:
    """Async client for Asana API operations."""
    
    def __init__(self, token: str):
        """Initialize the Asana client.
        
        Args:
            token: Asana Personal Access Token
        """
        self.token = token
        self.client = httpx.AsyncClient(
            base_url="https://app.asana.com/api/1.0",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
    
    async def get_workspaces(self) -> list[dict[str, Any]]:
        """Get all workspaces for the authenticated user.
        
        Returns:
            List of workspace dictionaries with 'gid' and 'name' fields
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        logger.debug("Fetching workspaces from Asana API")
        response = await self.client.get("/workspaces")
        response.raise_for_status()
        data = response.json()
        workspaces = data.get('data', [])
        logger.debug(f"Found {len(workspaces)} workspaces")
        return workspaces
    
    async def get_projects(self, workspace_id: str) -> list[dict[str, Any]]:
        """Get all active (non-archived) projects in a workspace.
        
        Args:
            workspace_id: The GID of the workspace
            
        Returns:
            List of project dictionaries with 'gid' and 'name' fields (only non-archived)
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        logger.debug(f"Fetching projects for workspace {workspace_id}")
        response = await self.client.get(
            f"/workspaces/{workspace_id}/projects",
            params={"opt_fields": "gid,name,archived"}
        )
        response.raise_for_status()
        data = response.json()
        all_projects = data.get('data', [])
        
        # Filter out archived projects
        active_projects = [p for p in all_projects if not p.get('archived', False)]
        
        logger.debug(f"Found {len(all_projects)} total projects, {len(active_projects)} active in workspace {workspace_id}")
        return active_projects
    
    async def _make_request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        **kwargs
    ) -> dict[str, Any]:
        """Make an API request with retry logic for rate limiting and transient errors.
        
        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            url: URL path (relative to base_url)
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments to pass to the request
            
        Returns:
            JSON response data
            
        Raises:
            httpx.HTTPError: If the request fails after all retries
        """
        for attempt in range(max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
                
                # Exponential backoff for transient errors
                wait_time = 2 ** attempt
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        # This should never be reached, but just in case
        raise httpx.HTTPError("Request failed after all retries")
    
    async def get_project_tasks(self, project_id: str) -> list[dict[str, Any]]:
        """Get all tasks in a project, sorted by creation date.
        
        Args:
            project_id: The GID of the project
            
        Returns:
            List of task dictionaries sorted by created_at (ascending)
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        logger.debug(f"Fetching tasks for project {project_id}")
        
        data = await self._make_request_with_retry(
            "GET",
            f"/projects/{project_id}/tasks",
            params={
                "opt_fields": "gid,name,created_at,parent,num_subtasks"
            }
        )
        
        tasks = data.get('data', [])
        
        # Sort by creation date (ascending)
        tasks.sort(key=lambda t: t.get('created_at', ''))
        
        logger.debug(f"Found {len(tasks)} tasks in project {project_id}")
        return tasks
    
    async def get_task_subtasks(self, task_id: str) -> list[dict[str, Any]]:
        """Get all subtasks of a task.
        
        Args:
            task_id: The GID of the parent task
            
        Returns:
            List of subtask dictionaries
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        logger.debug(f"Fetching subtasks for task {task_id}")
        
        data = await self._make_request_with_retry(
            "GET",
            f"/tasks/{task_id}/subtasks",
            params={
                "opt_fields": "gid,name,created_at,parent"
            }
        )
        
        subtasks = data.get('data', [])
        
        # Sort by creation date (ascending)
        subtasks.sort(key=lambda t: t.get('created_at', ''))
        
        logger.debug(f"Found {len(subtasks)} subtasks for task {task_id}")
        return subtasks
    
    async def update_task_name(self, task_id: str, new_name: str) -> dict[str, Any]:
        """Update the name of a task.
        
        Args:
            task_id: The GID of the task to update
            new_name: The new name for the task
            
        Returns:
            Updated task data
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        logger.debug(f"Updating task {task_id} name to: {new_name}")
        
        data = await self._make_request_with_retry(
            "PUT",
            f"/tasks/{task_id}",
            json={
                "data": {
                    "name": new_name
                }
            }
        )
        
        logger.info(f"Successfully updated task {task_id}")
        return data.get('data', {})
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
