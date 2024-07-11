import json
import uuid

from typing import Annotated

from fastapi import Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from langchain.output_parsers import OutputFixingParser
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.pydantic_v1 import ValidationError
from loguru import logger
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from lab_gen.datatypes.calls import Call
from lab_gen.services.conversation.conversation import ConversationMetadata, ConversationService
from lab_gen.services.conversation.dependencies import conversation_provider
from lab_gen.services.llm.lifetime import get_llm
from lab_gen.services.llm.parsers import StrictJsonOutputParser
from lab_gen.services.metrics.dependencies import metrics_provider
from lab_gen.services.metrics.metrics import Metric, MetricsService
from lab_gen.web.api import constants
from lab_gen.web.api.conversation.views import (
    CONVERSATION_ID,
    ConversationRequest,
)
from lab_gen.web.auth import get_api_key


router = APIRouter()

key_check = Annotated[bool, Depends(get_api_key)]
conversation_service = Annotated[ConversationService, Depends(conversation_provider)]
metrics_service = Annotated[MetricsService, Depends(metrics_provider)]

lenient_parser = JsonOutputParser(pydantic_object=Call)
strict_parser = StrictJsonOutputParser(pydantic_object=Call)

STRUCTURED_PROMPT = "structured_call_summary"

@router.post(
    "/structured/call",
    tags=["structured"],
    responses={
        200: {
            "description": constants.success200,
            "content": {
                "application/json": {
                    "example": {
                        "driver": {
                            "drivingLicenceNumber": "string",
                            "title": "string",
                            "firstNames": "string",
                            "lastName": "string",
                            "dateOfBirth": "string",
                            "postcode": "string",
                        },
                        "vehicle": {
                            "id": "string",
                            "make": "string",
                            "model": "string",
                            "colour": "string",
                            "registrationDocumentId": "stringstrin",
                        },
                        "startTime": "string",
                        "endTime": "string",
                        "participants": "string",
                        "topics": "string",
                        "summary": "string",
                        "actions": "string",
                        "category": [
                            "Vehicle",
                        ],
                        "sentiment": "string",
                    },
                },
            },
        },
        422: {"description": constants.error422},
        500: {"description": constants.error500},
        503: {"description": constants.error503},
    },
)
async def call_handler(
    request: ConversationRequest,
    x_business_user: Annotated[str, Header()],
    *,
    api_key: key_check,  # noqa: ARG001
    conversation: conversation_service,
    metrics: metrics_service,
) -> JSONResponse:
    """Returns structured response."""
    try:
        conversation_id = str(uuid.uuid4())  # Generate a new UUID
        meta = ConversationMetadata(provider=request.provider, variant=request.variant, business_user=x_business_user)
        llm = get_llm(request.provider, request.variant)

        input_variables = {"user_id": x_business_user, "format_instructions": lenient_parser.get_format_instructions()}
        if request.variables:
            input_variables.update(request.variables)

        if llm:
            config = conversation.generate_config(meta, conversation_id, llm)
            prompt = conversation.get_prompt(STRUCTURED_PROMPT)
            messages = [
                HumanMessagePromptTemplate(prompt=prompt),
            ]
            chat_prompt = ChatPromptTemplate.from_messages(messages)
            chain_with_history = conversation.create_chain(llm, chat_prompt).with_config(
                {"metadata": {"prompt_id": STRUCTURED_PROMPT}},
            )
            response = chain_with_history.invoke(input_variables, config=config)

            try:
                # This is a work-around because the JsonOutputParser didn't work in a chain.
                # So we use the StrOutputParser to get the response and then parse it as json.
                response_json = lenient_parser.parse(response)
                # The following parser is stricter and would throw a ValidationError if the json is not valid.
                Call.parse_obj(response_json)
                # Successfully produced valid json on first attempt.
                metrics.increment(Metric.COUNT_SUCCESSFUL_JSON, config["configurable"]["metadata"])
            except ValidationError:
                logger.debug("Before: " + json.dumps(response_json, sort_keys=True, indent=4))

                """
                TEMPORARY CHANGE TO STRICT PARSER PROMPT
                Awaiting Langchain fix to a bug causing the parser to fail
                due to expecting 'input' and not 'completion'.
                https://github.com/langchain-ai/langchain/pull/23967
                When PR is merged and released, the input variable can be reverted to 'completion'
                in the STRICT_FIX prompt in parsers.py and this comment can be removed.
                """
                fixing_parser = OutputFixingParser.from_llm(
                    llm=llm,
                    parser=strict_parser,
                    prompt=strict_parser.prompt,
                    max_retries=2,
                )
                response_json = fixing_parser.parse(response_json)
                logger.debug("After: " + json.dumps(response_json, sort_keys=True, indent=4))
                # Successfully produced valid json using fixer.
                metrics.increment(Metric.COUNT_FIXED_JSON, config["configurable"]["metadata"])
            except OutputParserException as ope:
                # This is an unrecoverable parsing error.
                logger.warning("Output Parser error: {0}", response)
                metrics.increment(Metric.COUNT_FAILED_JSON, config["configurable"]["metadata"])
                raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, constants.error_invalid_json_output) from ope

            metrics.record_llm_metrics(config["callbacks"][0], config["configurable"]["metadata"])
            return JSONResponse(content=response_json, headers={CONVERSATION_ID: conversation_id})
        else:  # noqa: RET505
            logger.warning("Unable to create llm.")
            raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, constants.error501)  # noqa: TRY301
    except Exception as e:
        logger.exception("Conversation Chain error")
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, constants.error501) from e
