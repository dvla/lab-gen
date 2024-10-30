from fastapi import Depends, HTTPException, Query
from fastapi.routing import APIRouter
from langchain_core.output_parsers import JsonOutputParser

from lab_gen.services.conversation.conversation import ConversationService
from lab_gen.services.conversation.dependencies import conversation_provider
from lab_gen.web.api.structured.views import STRUCTURED
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
        # Retrieve the prompt template from the conversation service
        prompt_template = conversation.get_prompt(prompt_id)
        # Access the main template
        template = prompt_template.template  # type: ignore[attr-defined]
        # Check if the prompt_id is in the STRUCTURED dictionary as a value in the "prompt" field
        schema = next((value["schema"] for value in STRUCTURED.values() if value["prompt"] == prompt_id), None)
        # If schema is found, add format instructions to the prompt
        if schema:
            lenient_parser = JsonOutputParser(pydantic_object=schema)
            format_instructions = lenient_parser.get_format_instructions()
            prompt = template.replace("{format_instructions}", format_instructions)
        else:
            prompt = template

        response = {
            "prompt": prompt,
        }
    except KeyError as err:
        # Raise an HTTPException if the prompt ID is not found
        raise HTTPException(status_code=404, detail="Prompt not found") from err
    else:
        return response
