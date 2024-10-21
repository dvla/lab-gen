from fastapi import Depends, HTTPException, Query
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
    show: str | None = Query(default=None, description="The category of prompts to show."),
) -> dict[str, list[str]]:
    """Returns available prompts.

    Returns:
        Mapping of prompt names to prompt texts.
    """
    return conversation.get_prompts(show)

@router.get("/prompts/{prompt_id}")
async def read_prompt(  # noqa: D417
    *,
    api_key: bool = Depends(get_api_key),  # noqa: ARG001
    conversation: ConversationService = Depends(conversation_provider),  # noqa: B008
    prompt_id: str,
) -> dict[str, str]:
    """Get prompt contents by prompt ID.

    Args:
        prompt_id: The ID of the prompt to retrieve.

    Returns:
        Prompt contents for a given prompt ID.
    """
    try:
        prompt_template = conversation.get_prompt(prompt_id)
        return {"prompt": prompt_template.pretty_repr()}
    except KeyError:
        raise HTTPException(status_code=404, detail="Prompt not found")  # noqa: B904
