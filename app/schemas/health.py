"""Health check response schema."""

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Worker health status."""

    model_config = ConfigDict(extra="forbid")

    model_loaded: bool
    gpu_available: bool
    cuda_version: str | None = None
    torch_version: str
    model_id: str
    uptime_seconds: float = Field(ge=0)
