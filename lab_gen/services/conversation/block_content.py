

from abc import ABC
from typing import Any

from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables.history import RunnableWithMessageHistory
from openai import BadRequestError


AZURE_CONTENT_FILTER_REASON = "content_filter"


class BlockedContentTracker(ABC, BaseCallbackHandler):
    """A callback handler that handles the blocked content instances in a conversation service."""
    def __init__(self, llm: BaseLanguageModel) -> None:
        """
        Initialize the blocked content tracker.

        Parameters:
            llm (BaseLanguageModel): The BaseLanguageModel instance to be used.

        Returns:
            None
        """
        self.llm = llm
        self.has_blocked = False

class AzureBlockedContentTracker(BlockedContentTracker):
    """A callback handler specific to Azure that handles the blocked content instances."""
    def on_llm_end(self, response: RunnableWithMessageHistory, **kwargs: Any) -> None: # noqa: ARG002, ANN401
        """
        A function that handles the end of a Azure LLM request with possible blocked content.

        Args:
            response (RunnableWithMessageHistory): The response object containing message history.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None
        """
        if (isinstance(response.generations, list)
            and response.generations[0][0].generation_info.get("finish_reason") == AZURE_CONTENT_FILTER_REASON):
            self.has_blocked = True

    def on_llm_error(self, error: BaseException,  **kwargs: Any) -> None: # noqa: ARG002, ANN401
        """
        Handles error and sets 'has_blocked' if the error is a BadRequestError with the content_filter reason.

        Args:
            error (BaseException): The error to handle.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None
        """
        if isinstance(error, BadRequestError) and error.code == AZURE_CONTENT_FILTER_REASON:
            self.has_blocked = True

class VertexBlockedContentTracker(BlockedContentTracker):
    """A callback handler specific to Vertex that handles the blocked content instances in a conversation service."""
    def on_llm_end(self, response: RunnableWithMessageHistory, **kwargs: Any) -> None: # noqa: ARG002, ANN401
        """
        A function that handles the end of a VertexLLM request with possible blocked content.

        Args:
            response (RunnableWithMessageHistory): The response object containing message history.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None
        """
        if (isinstance(response.generations, list) and response.generations[0]
            and (safety_ratings := response.generations[0][0].generation_info.get("safety_ratings", []))
            and any(rating.get("blocked", False) for rating in safety_ratings if isinstance(rating, dict))):
                self.has_blocked = True
