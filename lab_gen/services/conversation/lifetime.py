import os

from pathlib import Path

from fastapi import FastAPI
from langchain_core.prompts import BasePromptTemplate
from langchain_core.prompts.loading import load_prompt
from loguru import logger

from lab_gen.services.conversation.conversation import ConversationService
from lab_gen.settings import settings


def load_prompts() -> tuple[dict[str, list[str]], dict[str, BasePromptTemplate]]:
    """Loads the prompts from the prompts directory."""
    prompts = {}
    examples = {}
    try:
        for root, _dirs, files in os.walk(settings.prompts_dir):
            for file in files:
                if not file.startswith("_") and file.endswith(".json"):
                    file_path = Path(root) / file
                    logger.info(f"Loading file: {file_path}")
                    file_key = file_path.stem.lower()
                    prompt = load_prompt(file_path)
                    if file_path.parent.name == "examples":
                        examples[file_key] = prompt.input_variables
                    prompts[file_key] = prompt
    except Exception:
        logger.exception("Failed to load prompts")
        raise
    return examples, prompts


async def init_conversation(app: FastAPI) -> None:  # pragma: no cover
    """Initialize the conversation provider."""
    examples, prompts = load_prompts()
    app.state.conversation_provider = ConversationService(app, examples, prompts)
