from enum import Enum
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter()


class HealthStatus(str, Enum):
    """Represents the health status options for the application."""

    UP = "UP"
    UNKNOWN = "UNKNOWN"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class Health(BaseModel):
    """Represents the health status of the application."""

    status: HealthStatus = Field(default=HealthStatus.UNKNOWN, description="The health status of the application")
    description: str | None = Field(default=None, description="Description of the status")
    detail: dict[str, Any] = Field(description="Additional details about the health status")
