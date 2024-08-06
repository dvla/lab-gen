import time

from typing import Any

from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables.history import RunnableWithMessageHistory
from loguru import logger


class LLMMetricsCounter(BaseCallbackHandler):
    """A callback handler that counts the number of tokens used in a conversation service."""
    def __init__(self, llm: BaseLanguageModel) -> None:
        self.llm = llm
        self.input_tokens = 0
        self.output_tokens = 0
        self._start_time = 0
        self.request_duration_seconds = 0

    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> None: # noqa: ARG002, ANN401
        """
        Update input tokens based on prompts using the provided LLM model.

        :param serialized: The serialized data.
        :param prompts: A list of prompts.
        :param kwargs: Additional keyword arguments.
        :return: None
        """
        for p in prompts:
            self.input_tokens += self.llm.get_num_tokens(p)

        self._start_time = time.time()


    def on_llm_end(self, response: RunnableWithMessageHistory, **kwargs: Any)  -> None: # noqa: ARG002, ANN401
        """
        Updates output tokens when the LLM process ends.

        :param response: RunnableWithMessageHistory object
        :param kwargs: Additional keyword arguments
        :return: None
        """
        results = response.flatten()
        for r in results:
            self.output_tokens = self.llm.get_num_tokens(r.generations[0][0].text)

        self.request_duration_seconds = time.time() - self._start_time
        logger.debug(f"Request took {self.request_duration_seconds} seconds.")
