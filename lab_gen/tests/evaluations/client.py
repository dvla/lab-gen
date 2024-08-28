from dotenv import load_dotenv
from langchain_core.language_models import BaseLanguageModel

from lab_gen.datatypes.models import Model
from lab_gen.services.llm.lifetime import get_llm, init_models


load_dotenv(override=True)
init_models()

def get_client(client_config: dict) -> BaseLanguageModel:
    """
    Returns an instance of the llm client.

    Returns:
        BaseLanguageModel: An instance of the language model client.
    """
    key = Model.compute_key(provider=client_config["provider"],
                            variant=client_config["variant"],
                            family=client_config["family"])
    return get_llm(key)
