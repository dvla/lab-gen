from fastapi import Request

from lab_gen.services.metrics.metrics import MetricsService


def metrics_provider(request: Request) -> MetricsService:  # pragma: no cover
    """Return the MetricsService instance from the request state."""
    return request.app.state.metrics_provider
