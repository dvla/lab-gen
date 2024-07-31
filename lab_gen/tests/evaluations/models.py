from dotenv import load_dotenv
from langchain_core.language_models import BaseLanguageModel

from lab_gen.datatypes.models import Model, ModelFamily, ModelProvider, ModelVariant
from lab_gen.services.llm.lifetime import get_llm, init_models


load_dotenv(override=True)
init_models()

def get_llm_client() -> BaseLanguageModel:
    """
    Returns an instance of the language model client.

    Returns:
        BaseLanguageModel: An instance of the language model client.
    """
    key = Model.compute_key(provider=ModelProvider.VERTEX, variant=ModelVariant.GENERAL, family=ModelFamily.GEMINI)
    return get_llm(key)

def get_eval_client() -> BaseLanguageModel:
    """
    Returns an instance of the evaluation client.

    Returns:
        BaseLanguageModel: An instance of the evaluation client.
    """
    key = Model.compute_key(provider=ModelProvider.VERTEX, variant=ModelVariant.ADVANCED, family=ModelFamily.GEMINI)
    return get_llm(key)
