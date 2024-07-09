import uuid

from typing import Annotated, get_origin

from fastapi import Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from lab_gen.datatypes.calls import Call
from lab_gen.services.conversation.conversation import ConversationMetadata, ConversationService
from lab_gen.services.conversation.dependencies import conversation_provider
from lab_gen.services.llm.lifetime import get_llm
from lab_gen.services.metrics.dependencies import metrics_provider
from lab_gen.services.metrics.metrics import Metric, MetricsService
from lab_gen.web.api import constants
from lab_gen.web.api.conversation.streaming_with_status import StreamingResponseWithStatusCode
from lab_gen.web.api.conversation.views import (
    CONVERSATION_ID,
    ConversationFileStartRequest,
    stream_chain_response,
)
from lab_gen.web.auth import get_api_key


SYSTEM_MESSAGE = SystemMessage(
    content="You are a helpful AI bot, gifted at answering questions about images.",
)

router = APIRouter()

key_check = Annotated[bool, Depends(get_api_key)]
conversation_service = Annotated[ConversationService, Depends(conversation_provider)]
metrics_service = Annotated[MetricsService, Depends(metrics_provider)]

parser = JsonOutputParser(pydantic_object=Call)


@router.post(
    "/image",
    tags=["files"],
    responses={
        200: {"description": constants.success200},
        400: {"description": constants.error400},
        429: {"description": constants.error429},
        500: {"description": constants.error500},
        503: {"description": constants.error503},
    },
)
async def start_file_conversation(  # noqa: D417
    start: ConversationFileStartRequest,
    x_business_user: Annotated[str, Header()],
    *,
    api_key: key_check,
    conversation: conversation_service,
    metrics: metrics_service,
) -> StreamingResponse:
    """Starts a new conversation.

    This initializes a new image based conversation with the specified model provider and variant.
    An image file can be sent as a base64 encoded string.
    The content type of the file is specified using fileContentType.

    Arguments:
        provider: The model provider to use. Defaults to AZURE.
        variant: The variant of the model to use. Defaults to GENERAL.
        content: The string contents of the message.
        variables: Map of variable names and values.
        promptId: The ID of the prompt to use.
        x_business_user: business user ID header.
        file: The image file to send in base64.
        fileContentType: The content type of the file.

    Returns:
        The response from the LLM.

    Example File call:
    ```
    {
      "content": "What's this?",
      "provider": "AZURE",
      "variant": "MULTIMODAL",
      "file": "/9j/2wBDAAYEBQYFBAYGBQYHBwYIChAWgbAZNZxWB1rasA//2Q==",
      "fileContentType": "image/png"
    }
    ```

    """
    logger.debug(f"Has api key {api_key}")
    try:
        meta = ConversationMetadata(provider=start.provider, variant=start.variant, business_user=x_business_user)

        input_variables = {"user_id": x_business_user}

        conversation_id = str(uuid.uuid4())  # Generate a new UUID
        llm = get_llm(meta.provider, meta.variant)
        content = start.variables.get("input") if start.content is None else start.content

        if llm:
            messages = [SYSTEM_MESSAGE]
            if start.file is not None:
                # I had a problem with detecting the optional file string,
                # the `is_a_file` logic below works.
                is_a_file = get_origin(start.file) != Annotated
                if is_a_file:
                    if start.fileContentType is None:
                        msg = "ContentType is required when file is provided"
                        raise ValueError(msg)  # noqa: TRY301
                    image_message = {
                        "type": "image_url",
                        "image_url": {"url": f"data:{start.fileContentType.value};base64,{start.file}"},
                    }
                    text_message = {
                        "type": "text",
                        "text": content,
                    }
                    messages.append(HumanMessage(content=[text_message, image_message]))

            else:
                messages.append(("human", content))

            chat_prompt = ChatPromptTemplate.from_messages(messages)
            chain = conversation.create_chain(llm, chat_prompt)
            conversation.app.state.metrics_provider.increment(Metric.COUNT_CHAT_REQUESTS, meta.model_dump())

            config = conversation.generate_config(meta, conversation_id, llm)
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
        else:  # noqa: RET505
            logger.warning("Unable to create llm.")
            raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, constants.error501)  # noqa: TRY301
    except Exception as e:
        logger.exception("Conversation Chain error")
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, constants.error503) from e
