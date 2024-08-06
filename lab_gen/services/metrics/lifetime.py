from fastapi import FastAPI

from lab_gen.services.metrics.metrics import MetricsService


def init_metrics(app: FastAPI) -> None:
    """
    Initialize metrics for the given FastAPI app.

    Args:
        app (FastAPI): The FastAPI instance to initialize metrics for.

    Returns:
        None: This function does not return anything.
    """
    metrics_service = MetricsService(app)
    metrics_service.setup_metrics()
    app.state.metrics_provider = metrics_service
