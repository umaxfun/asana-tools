"""Configuration models with Pydantic validation."""

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Configuration for a single Asana project.
    
    Attributes:
        code: Project code (2-5 uppercase letters)
        asana_id: Asana project ID
    """
    code: str = Field(..., min_length=2, max_length=5, pattern=r'^[A-Z]{2,5}$')
    asana_id: str = Field(..., min_length=1)
    
    model_config = {
        'frozen': False,
        'str_strip_whitespace': True,
    }


class Config(BaseModel):
    """Main configuration for aa tool.
    
    Attributes:
        asana_token: Asana Personal Access Token
        interactive: Whether to use interactive mode (deprecated, kept for compatibility)
        projects: List of project configurations
    """
    asana_token: str = Field(..., min_length=1)
    interactive: bool = Field(default=False)
    projects: list[ProjectConfig] = Field(..., min_items=1)
    
    model_config = {
        'frozen': False,
        'str_strip_whitespace': True,
    }
