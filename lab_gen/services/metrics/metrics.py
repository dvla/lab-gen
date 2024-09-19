
from enum import Enum

from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import FastAPI
from loguru import logger
from opentelemetry import metrics
from opentelemetry.sdk.metrics import Counter, Histogram

from lab_gen.services.metrics.llm_metrics_counter import LLMMetricsCounter
from lab_gen.settings import settings


class Metric(Enum):
    """Represents different model providers."""

    COUNT_CHAT_REQUESTS = "chat_requests_counter"
    COUNT_PROMPT_TOKENS = "prompt_tokens_counter"
    COUNT_COMPLETION_TOKENS = "completion_tokens_counter"
    COUNT_ERRORS = "error_code_counter"
    COUNT_CONTENT_FILTERED = "content_filtered_counter"
    TIMER_LLM_REQUESTS = "llm_request_timer"
    COUNT_SUCCESSFUL_JSON = "successful_json_counter"
    COUNT_FIXED_JSON = "fixed_json_counter"
    COUNT_FAILED_JSON = "failed_json_counter"
    COUNT_VOTE_UP = "feedback_positive_counter"
    COUNT_VOTE_DOWN = "feedback_negative_counter"


class MetricsService:
    """Represents a metrics service."""

    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def setup_metrics(self) -> None:
        """Set up the metrics for Azure Monitor."""
        if settings.azure_monitor_connection_string:
            # Configure Azure Monitor with the connection string from settings
            configure_azure_monitor(connection_string=settings.azure_monitor_connection_string)
        else:
            logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not found. Metrics will not be collected.")

        # Get a meter with the name "lab-gen-metrics"
        meter = metrics.get_meter_provider().get_meter("lab-gen-metrics")

        # Store the histograms and counters in the app state
        setattr(self._app.state, Metric.COUNT_CHAT_REQUESTS.value,
                meter.create_counter(Metric.COUNT_CHAT_REQUESTS.value))
        setattr(self._app.state, Metric.COUNT_PROMPT_TOKENS.value,
                meter.create_histogram(Metric.COUNT_PROMPT_TOKENS.value))
        setattr(self._app.state, Metric.COUNT_COMPLETION_TOKENS.value,
                meter.create_histogram(Metric.COUNT_COMPLETION_TOKENS.value))
        setattr(self._app.state, Metric.COUNT_ERRORS.value,
                meter.create_counter(Metric.COUNT_ERRORS.value))
        setattr(self._app.state, Metric.TIMER_LLM_REQUESTS.value,
                meter.create_histogram(Metric.TIMER_LLM_REQUESTS.value))
        setattr(self._app.state, Metric.COUNT_CONTENT_FILTERED.value,
                meter.create_counter(Metric.COUNT_CONTENT_FILTERED.value))
        setattr(self._app.state, Metric.COUNT_SUCCESSFUL_JSON.value,
                meter.create_counter(Metric.COUNT_SUCCESSFUL_JSON.value))
        setattr(self._app.state, Metric.COUNT_FIXED_JSON.value,
                meter.create_histogram(Metric.COUNT_FIXED_JSON.value))
        setattr(self._app.state, Metric.COUNT_FAILED_JSON.value,
                meter.create_counter(Metric.COUNT_FAILED_JSON.value))
        setattr(self._app.state, Metric.COUNT_VOTE_UP.value,
                meter.create_counter(Metric.COUNT_VOTE_UP.value))
        setattr(self._app.state, Metric.COUNT_VOTE_DOWN.value,
                meter.create_counter(Metric.COUNT_VOTE_DOWN.value))

    def increment(self, metric: Metric, meta: dict, value: float = 1, custom_meta: dict[str, str] = {}) -> None:  # noqa: B006
        """
        Increment the given metrics counter by the specified value (default 1 if not provided).

        :param metric: The counter metric to be incremented.
        :type metric: Metric
        :param meta: Additional metadata for the metric increment.
        :type meta: dict
        :param value: The value to increment the counter by. Defaults to 1.
        :type value: float
        :return: None
        :rtype: None.
        """
        metric_name = metric.value
        if hasattr(self._app.state, metric_name):
            counter = getattr(self._app.state, metric_name)
            if isinstance(counter, Counter):
                metrics_meta = {
                    "business_user": meta["business_user"],
                    "environment": settings.environment,
                    "family": meta["family"].value,
                    "provider": meta["provider"].value,
                    "variant": meta["variant"].value,
                }
                metrics_meta.update(custom_meta)
                counter.add(value, metrics_meta)

    def record(self, metric: Metric, meta: dict, value: float) -> None:
        """
        Record the given metrics histogram by the specified value.

        :param metric: The histogram metric to record the value.
        :type metric: Metric
        :param value: The value to record on the histogram.
        :type value: float
        :param meta: Additional metadata for the histogram record.
        :type meta: dict
        :return: None
        :rtype: None.
        """
        metric_name = metric.value
        if hasattr(self._app.state, metric_name):
            histogram = getattr(self._app.state, metric_name)
            if isinstance(histogram, Histogram):
                histogram.record(value, {
                    "business_user": meta["business_user"],
                    "environment": settings.environment,
                    "family": meta["family"].value,
                    "provider": meta["provider"].value,
                    "variant": meta["variant"].value,
                })

    def record_llm_metrics(self, metric_counter: LLMMetricsCounter, meta: dict) -> None:
        """Record LLM metrics."""
        self.record(
            Metric.COUNT_PROMPT_TOKENS,
            meta,
            metric_counter.input_tokens,
        )
        self.record(
            Metric.COUNT_COMPLETION_TOKENS,
            meta,
            metric_counter.output_tokens,
        )
        self.record(
            Metric.TIMER_LLM_REQUESTS,
            meta,
            metric_counter.request_duration_seconds,
        )
