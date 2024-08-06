from fastapi import Depends
from fastapi.routing import APIRouter

from lab_gen.services.conversation.conversation import ConversationService
from lab_gen.services.conversation.dependencies import conversation_provider
from lab_gen.web.auth import get_api_key


router = APIRouter()


@router.get("/prompts/")
async def read_prompts(
    *,
    api_key: bool = Depends(get_api_key),  # noqa: ARG001
    conversation: ConversationService = Depends(conversation_provider),  # noqa: B008
) -> dict[str, list[str]]:
    """Returns available prompts.

    Returns:
        Mapping of prompt names to prompt texts.
    """
    return conversation.get_prompts()
