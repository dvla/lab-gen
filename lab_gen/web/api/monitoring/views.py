from fastapi import APIRouter
from starlette.requests import Request

from lab_gen.datatypes.health import Health, HealthStatus
from lab_gen.services.metrics.metrics import METRICS_AVAILABLE


router = APIRouter()


@router.get("/health", response_model_exclude_unset=True)
def health_check(request: Request) -> Health:
    """
    Checks the health of the application.

    It returns 200 if the application is healthy.
    """
    health_status = {}
    overall = HealthStatus.OUT_OF_SERVICE

    health_status["cosmos"] = (
        HealthStatus.UP if hasattr(request.app.state, "cosmos_client") else HealthStatus.OUT_OF_SERVICE
    )
    health_status["metrics"] = (
        HealthStatus.UP if hasattr(request.app.state, METRICS_AVAILABLE) else HealthStatus.OUT_OF_SERVICE
    )

    if all(status == HealthStatus.UP for status in health_status.values()):
        overall = HealthStatus.UP

    return Health(status=overall, detail=health_status)
