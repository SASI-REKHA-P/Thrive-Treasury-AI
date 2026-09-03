from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response payload."""
    status: str = Field(default="ok", description="Service health indicator")
    service: str = Field(default="thrive-treasury-ai", description="Service name identifier")
    version: str = Field(default="0.1.0", description="Service semantic version")
