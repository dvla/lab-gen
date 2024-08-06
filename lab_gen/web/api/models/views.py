
from collections.abc import AsyncGenerator
from typing import Annotated

import tiktoken

from fastapi import Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter
from loguru import logger
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_503_SERVICE_UNAVAILABLE

from lab_gen.datatypes.models import Model, ModelProvider, ModelVariant
from lab_gen.services.openai.lifetime import get_client
from lab_gen.settings import settings
from lab_gen.web.auth import get_api_key


error503 = "OpenAI server is busy"
error500 = "OpenAI Response (Streaming) Error"

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
encoding = tiktoken.get_encoding("cl100k_base")


class Message(BaseModel):
    """
    Represents a message in the chat conversation.

    Attributes:
        content (str): The content of the message.
            Defaults to "Ask me something".
        role (str): The role of the message author.
            Defaults to "user".
    """

    content: str = "Ask me something"
    """The contents of the message."""

    role: str = "user"
    """The role of the messages author, in this case `user`."""


class Chat(BaseModel):
    """
    Represents a chat conversation.

    Attributes:
        model_name (str): The name of the model used for chat processing.
        message (list[Message]): The list of messages exchanged in the conversation.
    """

    provider: ModelProvider = ModelProvider.AZURE
    variant: ModelVariant = ModelVariant.GENERAL
    messages: list[Message]


@router.get("/models/")
async def read_models() -> list[Model]:
    """
    Retrieves a list of model definitions.

    Returns:
        list[Model]: A list of Models representing the available models.
    """
    return settings.models + settings.models_vertex


@router.post(
    "/chat",
    tags=["chat"],
    response_class=StreamingResponse,
    responses={
        200: {"description": "Successful Response"},
        429: {"description": "The user has sent too many requests in a given amount of time"},
        500: {"description": error500},
        503: {"description": error503},
    },
)
@limiter.limit(settings.rate_limit_default)
async def chat_handler(
    chat: Chat,
    x_business_user: Annotated[str | None, Header()] = None,
    *,
    api_key: bool = Depends(get_api_key),
    request: Request,  # used by limiter
) -> StreamingResponse:
    """
    Asynchronously generates a stream of responses from the OpenAI chat model.

    Returns:
        A stream of responses from the OpenAI chat model.

    Raises:
        HTTPException: If there is an error in the OpenAI API response.
    """
    logger.debug(f"Has api key {api_key}")

    async def response_stream() -> AsyncGenerator[str, None]:
        completion_tokens = 0
        prompt_tokens = 0

        # Access the app instance from the request object
        app = request.app

        chat_requests_counter = app.state.chat_requests_counter
        prompt_tokens_counter = app.state.prompt_tokens_counter
        completion_tokens_counter = app.state.completion_tokens_counter

        # Calculate the number of tokens in the prompt
        for message in chat.messages:
            prompt_tokens += len(encoding.encode(message.content))

        try:
            client, model_name = get_client(chat.provider, chat.variant)
            logger.debug(f"User is {x_business_user} and Chat Model name is : {model_name}")
            stream = await client.chat.completions.create(
                model=model_name,
                messages=chat.messages,
                stream=True,
            )

            # Record the chat request metric with dimensions for business user, environment and model
            chat_requests_counter.add(1, {
                "business_user": x_business_user,
                "environment": settings.environment,
                "model_name": model_name,
            })
            # Record the prompt tokens metric
            prompt_tokens_counter.record(prompt_tokens, {
                "business_user": x_business_user,
                "environment": settings.environment,
                "model_name": model_name,
            })

        except Exception as e:
            logger.exception("Error from openAI")
            raise HTTPException(HTTP_503_SERVICE_UNAVAILABLE, error503) from e
        try:
            async for chunk in stream:
                if len(chunk.choices) > 0:
                    current_content = chunk.choices[0].delta.content
                    if current_content is not None:
                        # Calculate the number of tokens in the response
                        chunk_tokens = encoding.encode(current_content)
                        completion_tokens += len(chunk_tokens)
                        yield current_content
        except Exception as e:
            logger.exception("OpenAI Response (Streaming) Error")
            raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, error500) from e

        # Record the completion tokens metric
        completion_tokens_counter.record(completion_tokens, {
            "business_user": x_business_user,
            "environment": settings.environment,
            "model_name": model_name,
        })

    return StreamingResponse(response_stream(), media_type="text/plain; charset=utf-8")
