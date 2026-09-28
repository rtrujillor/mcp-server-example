"""Usage profile model."""
from typing import Optional

from pydantic import BaseModel, Field


class UsageProfile(BaseModel):
    """Represents expected usage patterns for cost estimation."""
    
    users: int = Field(description="Number of users")
    projects: Optional[int] = Field(default=None, description="Number of active projects")
    api_requests_per_month: Optional[int] = Field(default=None, description="Expected API calls per month")
