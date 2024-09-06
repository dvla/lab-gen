from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field
from starlette.status import (
    HTTP_404_NOT_FOUND,
)

from lab_gen.datatypes.errors import NoConversationError
from lab_gen.services.conversation.conversation import (
    ConversationService,
)
from lab_gen.services.conversation.dependencies import conversation_provider
from lab_gen.services.metrics.dependencies import metrics_provider
from lab_gen.services.metrics.metrics import Metric, MetricsService
from lab_gen.web.auth import get_api_key


router = APIRouter()
key_check = Annotated[bool, Depends(get_api_key)]
metrics_service = Annotated[MetricsService, Depends(metrics_provider)]
conversation_service = Annotated[ConversationService, Depends(conversation_provider)]


class ScoreDataType(str, Enum):
    """Represents the score data type."""

    NUMERIC = "NUMERIC"
    BOOLEAN = "BOOLEAN"
    CATEGORICAL = "CATEGORICAL"


class CreateScoreRequest(BaseModel):
    """Request to create a score."""

    conversationId: str = Field(  # noqa: N815
        ...,
        description="The unique conversation ID",
    )
    name: str = Field(
        ...,
        description="The name of the score. This may be the prompt_id or another identifier",
    )
    value: float | str = Field(
        ...,
        description="""
        The value of the score. Must be passed as string for categorical scores,
        and numeric for boolean and numeric scores. Boolean score values must equal either 1 or 0 (true or false)
        """,
    )
    data_type: ScoreDataType = Field(alias="dataType", default=ScoreDataType.BOOLEAN)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "joke",
                    "conversationId": "3c91774d-6b24-4d97-9ba2-93634cf30",
                    "value": 1,
                },
            ],
        },
    }


@router.post(
    "/scores",
    tags=["feedback"],
    response_class=StreamingResponse,
    responses={
        200: {"description": "Successful Response"},
        429: {"description": "The user has sent too many requests in a given amount of time"},
    },
)
def scores_handler(
    score: CreateScoreRequest,
    x_business_user: Annotated[str, Header()],
    *,
    api_key: key_check,  # noqa: ARG001
    metrics: metrics_service,
    conversation: ConversationService = Depends(conversation_provider),  # noqa: B008
) -> JSONResponse:
    """
    Submits a feedback score.

    It returns 200 if the score is recorded successfully.
    """
    meta = {
        "score_name": score.name,
    }
    history = conversation.get_message_history(user_id=x_business_user, conversation_id=score.conversationId)
    if history.metadata is None:
        raise HTTPException(HTTP_404_NOT_FOUND, str(NoConversationError(score.conversationId)))
    if score.value == 1:
        metrics.increment(Metric.COUNT_VOTE_UP, history.metadata.model_dump(), 1, meta)
    if score.value == 0:
        metrics.increment(Metric.COUNT_VOTE_DOWN, history.metadata.model_dump(), 1, meta)
    return JSONResponse(status_code=200, content={"message": "Score recorded successfully"})
