
from typing import Any

from fastapi import FastAPI
from loguru import logger
from openai import AsyncAzureOpenAI, AsyncOpenAI

from lab_gen.datatypes.models import AzureModelConfig, ModelFamily, ModelProvider, ModelVariant
from lab_gen.settings import settings


model_providers: dict[str, Any] = {}
model_names: dict[str, str] = {}


def get_client(provider: ModelProvider, variant: ModelVariant) -> tuple[AsyncOpenAI, str]:
    """
    Get the client for the specified model provider and variant.

    Args:
        provider (ModelProvider): The model provider.
        variant (ModelVariant): The model variant.

    Returns:
        BaseAzureClient: The client for the specified model provider and variant.

    Raises:
        KeyError: If the specified model provider and variant combination is not found.
    """
    key = provider.value + variant.value
    try:
        return model_providers[key], model_names[key]
    except KeyError:
        logger.warning(f"Unable to find model {key}")
    return None, None


def init_openai(app: FastAPI) -> None:  # noqa: ARG001
    """
    Loops through the model settings, for each model configures an AzureOpenAI client.

    :param app: current fastapi application.
    """
    for model in settings.models:
        if model.provider == (ModelProvider.AZURE
                              and model.family == ModelFamily.GPT
                              and model.config is not None):
            config = AzureModelConfig(**model.config)
            key = model.provider.value + model.variant.value
            client = AsyncAzureOpenAI(
                api_version=config.api_version,
                api_key=config.api_key,
                azure_endpoint=config.endpoint,
            )
            model_providers[key] = client
            model_names[key] = model.identifier
