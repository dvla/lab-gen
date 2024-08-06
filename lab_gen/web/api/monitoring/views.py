from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter()


class HealthStatus(str, Enum):
    """
    Represents the health status options for the application.

    The possible values are:
        - UP: Indicates that the application is up and running.
        - DOWN: Indicates that the application is currently down.
        - UNKNOWN: Indicates that the health status is unknown.
        - OUT_OF_SERVICE: Indicates that the application has been taken out of service.
    """

    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class Health(BaseModel):
    """Represents the health status of the application."""

    status: HealthStatus
    description: str | None = Field(default=None, description="Description of the status")

@router.get("/health", response_model_exclude_unset=True)
def health_check() -> Health:
    """
    Checks the health of the application.

    It returns 200 if the application is healthy.
    """
    return Health(status=HealthStatus.UP)
