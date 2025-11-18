"""Asana API client for async operations."""

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
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
