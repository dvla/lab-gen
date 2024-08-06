from typing import Any

import boto3

from google.oauth2 import service_account
from langchain_community.chat_models import BedrockChat
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.language_models import BaseLanguageModel
from langchain_google_vertexai import ChatVertexAI, HarmBlockThreshold, HarmCategory
from langchain_openai import AzureChatOpenAI
from loguru import logger

from lab_gen.datatypes.models import (
    AzureModelConfig,
    BedrockModelConfig,
    HuggingfaceModelConfig,
    ModelProvider,
    ModelVariant,
)
from lab_gen.settings import settings


MAX_TOKENS = 1536

VERTEX_SAFETY_CONFIG = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

model_providers: dict[str, Any] = {}


def get_llm(provider: ModelProvider, variant: ModelVariant) -> BaseLanguageModel | None:
    """
    Get the LLM for the specified model provider and variant.

    Args:
        provider (ModelProvider): The model provider.
        variant (ModelVariant): The model variant.

    Returns:
        BaseLanguageModel: The llm for the specified model provider and variant.

    Raises:
        KeyError: If the specified model provider and variant combination is not found.
    """
    key = provider.value + variant.value
    try:
        return model_providers[key]
    except KeyError as ke:
        logger.warning(f"Unable to find model {key}")
        raise KeyError(key) from ke
    return None


def init_models() -> None:
    """
    Loops through the model settings, for each model configures an LLM client.

    :param app: current fastapi application.
    """
    modelz = settings.models + settings.models_vertex
    for model in modelz:
        if model.config is not None:
            key = model.provider.value + model.variant.value
            llm = None
            match model.provider:
                case ModelProvider.AZURE:
                    config = AzureModelConfig(**model.config)
                    llm = AzureChatOpenAI(
                        verbose=True,
                        temperature=0,
                        model_name=model.identifier,
                        max_tokens=MAX_TOKENS,
                        api_version=config.api_version,
                        azure_endpoint=config.endpoint,
                        api_key=config.api_key,
                        streaming=True,
                    )
                case ModelProvider.BEDROCK:
                    config = BedrockModelConfig(**model.config)
                    boto_client = boto3.client(
                        service_name="bedrock-runtime",
                        **config.model_dump(),
                    )
                    llm = BedrockChat(
                        client=boto_client,
                        model_id=model.identifier,
                        streaming=True,
                        model_kwargs={"max_tokens": MAX_TOKENS},
                    )
                case ModelProvider.VERTEX:
                    credentials = service_account.Credentials.from_service_account_info(model.config)
                    vertex_setup = {
                        "credentials": credentials,
                        "model_name": model.identifier,
                        "project": model.config["project_id"],
                        "max_output_tokens": MAX_TOKENS,
                        "streaming": True,
                        "safety_settings": VERTEX_SAFETY_CONFIG,
                        "convert_system_message_to_human": True,
                    }
                    if "location" in model.config:
                        vertex_setup["location"] = model.config["location"]
                    llm = ChatVertexAI(**vertex_setup)
                case ModelProvider.HUGGINGFACE:
                    config = HuggingfaceModelConfig(**model.config)
                    llm = HuggingFaceEndpoint(
                        streaming=True,
                        repo_id=config.repo_id, huggingfacehub_api_token=config.access_token)
            if llm is not None:
                logger.debug(f"Configuring LLM for {key} {model.identifier}")
                model_providers[key] = llm

    if len(model_providers) != len(modelz):
        logger.warning(f"Configured {len(model_providers)} LLMs, but provided {len(modelz)} in settings")
