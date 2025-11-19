"""Pydantic models for Asana tasks."""

from datetime import datetime
from pydantic import BaseModel, Field


class AsanaTask(BaseModel):
    """Model for an Asana task."""
    
    gid: str = Field(..., description="Global ID of the task")
    name: str = Field(..., description="Name/title of the task")
    created_at: datetime = Field(..., description="When the task was created")
    parent: dict | None = Field(None, description="Parent task if this is a subtask")


class TaskUpdate(BaseModel):
    """Model for a task update operation."""
    
    task_id: str = Field(..., description="GID of the task being updated")
    old_name: str = Field(..., description="Original task name")
    new_name: str = Field(..., description="New task name with ID")
    assigned_id: str = Field(..., description="The ID that was assigned (e.g., PRJ-5)")
