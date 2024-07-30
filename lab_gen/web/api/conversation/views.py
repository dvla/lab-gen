from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter
from langchain_core.runnables.history import RunnableWithMessageHistory
from loguru import logger
from pydantic import BaseModel, EncodedStr, Field, model_validator
from pydantic.types import Base64UrlEncoder
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from lab_gen.datatypes.errors import InvalidParamsError, ModelKeyError, NoConversationError
from lab_gen.datatypes.metadata import ContentType
from lab_gen.datatypes.models import DEFAULT_MODEL_KEY
from lab_gen.services.conversation.conversation import (
    ConversationService,
)
from lab_gen.services.conversation.dependencies import conversation_provider
from lab_gen.services.metrics.dependencies import metrics_provider
from lab_gen.services.metrics.metrics import Metric, MetricsService
from lab_gen.web.api import constants
from lab_gen.web.api.conversation.streaming_with_status import StreamingResponseWithStatusCode
from lab_gen.web.auth import get_api_key


key_check = Annotated[bool, Depends(get_api_key)]
conversation_service = Annotated[ConversationService, Depends(conversation_provider)]
metrics_service = Annotated[MetricsService, Depends(metrics_provider)]

CONVERSATION_ID = "X-conversation-id"
BLOCKED_CONTENT_RESPONSE = "Your request was blocked due to content filtering. Please modify your prompt and retry."
OK_STATUS_CODE = 200
BAD_REQUEST_STATUS_CODE = 400

router = APIRouter()

class Message(BaseModel):
    """
    Represents a message in the chat conversation.

    Attributes:
        content (str): The content of the message.
            Defaults to "Ask me something".
        role (str): The role of the message author.
            Defaults to "user".
    """

    content: str | list[str | dict]
    """The string contents of the message."""

    type: str = "human"
    """The role of the messages author, in this case `user`."""


class ConversationRequest(BaseModel):
    """
    Base model for starting or continuing a conversation.

    Attributes:
        content (str | None): The string contents of the message. Defaults to None.
        modelKey (str): The unique key for the model to use.
        variables (dict[str, str] | None): Map of variable names and values. Defaults to None.
    """

    content: str | None = None
    modelKey: str = Field(DEFAULT_MODEL_KEY)  # noqa: N815
    variables: dict[str, str] | None = Field(None)

class ConversationContinueRequest(BaseModel):
    """
    Model for continuing an existing conversation with additional content.

    Attributes:
        content (str | None): The string contents of the continuation message. Defaults to None.
    """

    content: str | None = None

class ConversationStartRequest(ConversationRequest):
    """
    Model for initiating a new conversation with optional variables and specified model key.

    Attributes:
        promptId (str): The ID of the prompt to use. Defaults to "DEFAULT".
        modelKey (str): The unique key for the model to use.
        variables (dict[str, str] | None): Map of variable names and values. Defaults to None.
    """

    promptId: str = "DEFAULT"  # noqa: N815

    @model_validator(mode="after")
    def check_required(self) -> "ConversationStartRequest":
        """Validates that either content and/or variables is provided for starting a conversation."""
        content = self.content
        variables = self.variables
        if content is None and variables is None:
            msg = "content or variables is required."
            raise ValueError(msg)
        return self

class ConversationFileStartRequest(ConversationStartRequest):
    """
    Model for initiating a new file-based conversation. Extends ConversationStartRequest with file attributes.

    Attributes:
        promptId (str): The ID of the prompt to use. Defaults to "DEFAULT".
        file (str | None): The file to be used in the conversation, encoded as a base64 string. Defaults to None.
        fileContentType (ContentType | None): The content type of the file. Defaults to ContentType.PNG.
    """

    file: str | None = Annotated[str | None, EncodedStr(encoder=Base64UrlEncoder)]
    fileContentType: ContentType | None = ContentType.PNG  # noqa: N815

def get_error_message(exception: Exception) -> str:
    """Extracts an error message from an exception.

    Args:
        exception (Exception): The exception from which to extract the message.

    Returns:
        str: The extracted error message or a default exception.
    """
    try:
        # Attempt to extract the message from exception body
        return exception.body["message"]
    except AttributeError:
        # Fallback to a generic error message if attribute 'body' does not exist
        return str(exception)


async def stream_chain_response(
    chain: RunnableWithMessageHistory,
    variables: dict[str, str],
    config: dict,
    metrics: MetricsService,
) -> AsyncGenerator[tuple[str, int], None]:
    """Streams responses from a conversation chain along with status codes.

    This asynchronously generates responses and status codes from the conversation chain for the given input.
    It configures the chain to use the provided conversation ID as the session ID.
    It also counts the number of tokens used in the conversation and sends them to the metrics service.

    Args:
        chain: The conversation chain to stream responses from.
        variables: The input variables to provide to the chain.
        config (dict): The configuration dictionary.
        metrics (MetricsService, optional): The metrics service.

    Yields:
        AsyncGenerator[Tuple[str, int], None]: Tuples of response text and status codes streamed from the chain.
    """
    metric_counter = config["callbacks"][0]
    blocked_counter = config["callbacks"][1]
    meta = config["configurable"]["metadata"]

    try:
        async for chunk in chain.astream(variables, config=config):
            yield (chunk, OK_STATUS_CODE)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error occurred: {e}")

        if not blocked_counter.has_blocked:
            metrics.increment(Metric.COUNT_ERRORS, meta)
            yield (get_error_message(e), 500)

    if blocked_counter.has_blocked:
        metrics.increment(Metric.COUNT_CONTENT_FILTERED, meta)
        logger.warning(BLOCKED_CONTENT_RESPONSE)
        yield (BLOCKED_CONTENT_RESPONSE, BAD_REQUEST_STATUS_CODE)

    metrics.record_llm_metrics(metric_counter, meta)

@router.post(
    "/conversations",
    tags=["conversation"],
    responses={
        200: {"description": constants.success200},
        400: {"description": constants.error400},
        429: {"description": constants.error429},
        500: {"description": constants.error500},
        503: {"description": constants.error503},
    },
)
async def start_conversation(  # noqa: D417
    start: ConversationStartRequest,
    x_business_user: Annotated[str, Header()],
    *,
    api_key: key_check,
    conversation: conversation_service,
    metrics: metrics_service,
) -> StreamingResponse:
    """Starts a new conversation.

    This initializes a new conversation with the specified model key.
    It returns a conversation ID that can be used to continue the conversation.

    Arguments:
        modelKey: The unique key for the model to use.
        content: The string contents of the message.
        variables: Map of variable names and values.
        promptId: The ID of the prompt to use.
        x_business_user: business user ID header.

    Returns:
        The response from the LLM.

    Example Prompt call:
    ```
    {
        "modelKey": "AZUREGPTADVANCED",
        "promptId": "alliteration",
        "variables": {
            "input": "This is a great Lab demo. I feel I am learning lots"
        }
    }
    ```
    Example Joke Prompt call:
    ```
    {
        "promptId": "joke",
        "variables": {
            "joke_type": "Dad",
            "input": "Birds"
        }
    }
    ```
    Example Variant, get the model key from the call to GET /models:
    ```
    {
        "content": "When did AWS start?",
        "modelKey": "BEDROCKCLAUDEGENERAL"
    }
    ```
    Simple call:
    ```
    {
        "content": "What is the DVLA?"
    }
    ```

    """
    logger.debug(f"Has api key {api_key}")
    try:
        meta = conversation.get_metadata(model_key=start.modelKey, business_user=x_business_user)
        config, conversation_id, chain = conversation.start(
            meta,
            start.promptId.lower(),
        )
        input_variables = {"user_id": x_business_user}
        if start.variables:
            input_variables.update(start.variables)
        if start.content:
            input_variables.update({"input": start.content})
        return StreamingResponseWithStatusCode(
            stream_chain_response(
            chain,
            variables=input_variables,
            config=config,
            metrics=metrics,
            ),
            headers={CONVERSATION_ID: conversation_id},
            media_type=constants.TEXT_MEDIA_TYPE,
        )
    except ModelKeyError as ke:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(ke)) from ke
    except Exception as e:
        logger.exception("Conversation Chain error")
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, constants.error503) from e


@router.put(
    "/conversations/{conversationId}",
    tags=["conversation"],
    responses={
        200: {"description": constants.success200},
        400: {"description": constants.error400},
        429: {"description": constants.error429},
        404: {"description": constants.error404},
        503: {"description": constants.error503},
    },
    status_code=200,
)
async def continue_conversation(  # noqa: D417, PLR0913
    conversationId: str,  # noqa: N803
    convo: ConversationContinueRequest,
    x_business_user: Annotated[str, Header()],
    *,
    api_key: key_check,
    conversation: conversation_service,
    metrics: metrics_service,
) -> StreamingResponse:
    """Continues an existing conversation by sending a new message to the conversation and returning the response.

    Arguments:
        conversationId: The ID of the conversation to continue.
        content: The new message content to send to the conversation.

    Returns:
        The response from the LLM.

    Raises:
         HTTPException if the conversation is not found or a server error occurs.
    """
    logger.debug(f"Conversation api key {api_key}")
    try:
        config, chain = conversation.get(conversationId, x_business_user)
        return StreamingResponseWithStatusCode(
            stream_chain_response(chain, config=config, metrics=metrics, variables={"input": convo.content}),
            headers={CONVERSATION_ID: conversationId},
            media_type=constants.TEXT_MEDIA_TYPE,
        )
    except NoConversationError as nce:
        raise HTTPException(HTTP_404_NOT_FOUND, str(nce)) from nce
    except Exception as e:
        logger.exception("Conversation Chain error")
        raise HTTPException(HTTP_503_SERVICE_UNAVAILABLE, constants.error503) from e


@router.get(
    "/conversations/{conversationId}/history",
    tags=["conversation"],
    responses={
        200: {"description": constants.success200},
        404: {"description": constants.error404},
    },
    status_code=200,
)
async def conversation_history(  # noqa: D417
    conversationId: str,  # noqa: N803
    x_business_user: Annotated[str, Header()],
    *,
    api_key: bool = Depends(get_api_key),
    conversation: ConversationService = Depends(conversation_provider),  # noqa: B008
) -> list[dict[str, str]]:
    """Gets the message history for a conversation.

    Arguments:
        conversationId: The ID of the conversation to get history for.

    Returns:
        A list of Messages representing the conversation history.

    Raises:
         HTTPException if the conversation is not found.
    """
    try:
        logger.debug(f"History api key {api_key}")
        return conversation.history(x_business_user, conversationId)

    except NoConversationError as nce:
        raise HTTPException(HTTP_404_NOT_FOUND, str(nce)) from nce


@router.delete(
    "/conversations/{conversationId}",
    tags=["conversation"],
    responses={
        200: {"description": constants.success200},
        404: {"description": constants.error404},
    },
    status_code=200,
)
async def end_conversation(  # noqa: D417
    conversationId: str,  # noqa: N803
    x_business_user: Annotated[str, Header()],
    *,
    api_key: bool = Depends(get_api_key),
    conversation: ConversationService = Depends(conversation_provider),  # noqa: B008
) -> None:
    """Ends the conversation with the given ID.

    Arguments:
        conversationId: The ID of the conversation to end.
    """
    try:
        logger.debug(f"End conversation api key {api_key}")
        conversation.end(x_business_user, conversationId)

    except NoConversationError as nce:
        raise HTTPException(HTTP_404_NOT_FOUND, str(nce)) from nce


@router.delete(
    "/conversations/{conversationId}/history/{num_entries}",
    tags=["conversation"],
    responses={
        200: {"description": constants.success200},
        404: {"description": constants.error404},
        400: {"description": constants.error400},
    },
    status_code=200,
)
async def delete_history_entry(
    conversationId: str,  # noqa: N803
    num_entries: int,
    x_business_user: Annotated[str, Header()],
    *,
    conversation: ConversationService = Depends(conversation_provider),  # noqa: B008
) -> None:
    """
    Delete an entry from a conversation's history.

    An entry is defined as a conversation pair of human and ai messages.
    e.g. if you provide num_entries=1 then 1 pair is deleted from the end of the history.

    Args:
        conversationId (str): The ID of the conversation.
        num_entries (int): The number of entries in the conversation history to delete from the end.
        x_business_user (str): The business user ID from the header.
        conversation: The conversation object that contains the history entry to be deleted.

    Raises:
        HTTPException: 404 error if the conversation does not exist.
        HTTPException: 400 error if the num_entries parameter is not an integer.
    """
    try:
        conversation.delete_history(x_business_user, conversationId, num_entries)
    except NoConversationError as nce:
        raise HTTPException(HTTP_404_NOT_FOUND, str(nce)) from nce
    except InvalidParamsError as ipe:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(ipe)) from ipe
