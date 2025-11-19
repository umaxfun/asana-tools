"""Cache models with Pydantic validation."""

from pydantic import BaseModel, Field


class ProjectCache(BaseModel):
    """Cache data for a single project.
    
    Tracks the last assigned IDs for root tasks and subtasks.
    
    Attributes:
        last_root: Last assigned root task number (e.g., 42 for PRJ-42)
        subtasks: Mapping of parent ID (without project code) to last subtask number
                  Example: {"5": 3} means PRJ-5-3 was the last subtask of PRJ-5
                          {"12-2": 4} means PRJ-12-2-4 was the last subtask of PRJ-12-2
    """
    last_root: int = Field(default=0, ge=0)
    subtasks: dict[str, int] = Field(default_factory=dict)
    
    model_config = {
        'frozen': False,
    }


class CacheData(BaseModel):
    """Main cache data structure.
    
    Stores cache information for all projects, keyed by project code.
    
    Attributes:
        projects: Mapping of project code to project cache data
                  Example: {"PRJ": ProjectCache(...), "TSK": ProjectCache(...)}
    
    Example cache structure:
        {
            "projects": {
                "PRJ": {
                    "last_root": 42,
                    "subtasks": {
                        "5": 3,      # PRJ-5-3
                        "12": 7,     # PRJ-12-7
                        "12-2": 4    # PRJ-12-2-4
                    }
                },
                "TSK": {
                    "last_root": 15,
                    "subtasks": {}
                }
            }
        }
    """
    projects: dict[str, ProjectCache] = Field(default_factory=dict)
    
    model_config = {
        'frozen': False,
    }
