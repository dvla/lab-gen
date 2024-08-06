from collections.abc import AsyncGenerator
from typing import Any

import azure.core.credentials_async
import openai
import pytest

from fastapi import FastAPI
from httpx import AsyncClient

from lab_gen.web.application import get_app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Backend for anyio pytest plugin.

    :return: backend name.
    """
    return "asyncio"


@pytest.fixture()
def fastapi_app() -> FastAPI:
    """
    Fixture for creating FastAPI app.

    :return: fastapi app with mocked dependencies.
    """
    return get_app()


@pytest.fixture()
async def client(
    fastapi_app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates client for requesting server.

    :param fastapi_app: the application.
    :yield: client for the app.
    """
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def mock_openai_chatcompletion(monkeypatch) -> None:  # noqa: PT004, ANN001
    """
    A pytest fixture that mocks the openai chat completion for testing purposes.

    Args:
        monkeypatch: The monkeypatch object for patching the openai resources.

    Returns:
        None
    """
    class AsyncChatCompletionIterator:
        def __init__(self, answer: str) -> None:
            """Initializes the ChatCompletionChunk with the given answer and sets the initial chunk index and chunks."""
            self.chunk_index = 0
            self.chunks = [
                # This is an Azure-specific chunk solely for prompt_filter_results
                openai.types.chat.ChatCompletionChunk(
                    object="chat.completion.chunk",
                    choices=[],
                    id="",
                    created=0,
                    model="",
                    prompt_filter_results=[
                        {
                            "prompt_index": 0,
                            "content_filter_results": {
                                "hate": {"filtered": False, "severity": "safe"},
                                "self_harm": {"filtered": False, "severity": "safe"},
                                "sexual": {"filtered": False, "severity": "safe"},
                                "violence": {"filtered": False, "severity": "safe"},
                            },
                        },
                    ],
                ),
                openai.types.chat.ChatCompletionChunk(
                    id="test-123",
                    object="chat.completion.chunk",
                    choices=[
                        openai.types.chat.chat_completion_chunk.Choice(
                            delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(content=None, role="assistant"),
                            index=0,
                            finish_reason=None,
                            # Only Azure includes content_filter_results
                            content_filter_results={},
                        ),
                    ],
                    created=1703462735,
                    model="gpt-35-turbo",
                ),
            ]
            answer_deltas = answer.split(" ")
            for answer_index, answer_delta in enumerate(answer_deltas):
                # Completion chunks include whitespace, so we need to add it back in
                if answer_index > 0:
                    answer_delta = " " + answer_delta  # noqa: PLW2901
                self.chunks.append(
                    openai.types.chat.ChatCompletionChunk(
                        id="test-123",
                        object="chat.completion.chunk",
                        choices=[
                            openai.types.chat.chat_completion_chunk.Choice(
                                delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(
                                    role=None, content=answer_delta,
                                ),
                                finish_reason=None,
                                index=0,
                                logprobs=None,
                                # Only Azure includes content_filter_results
                                content_filter_results={
                                    "hate": {"filtered": False, "severity": "safe"},
                                    "self_harm": {"filtered": False, "severity": "safe"},
                                    "sexual": {"filtered": False, "severity": "safe"},
                                    "violence": {"filtered": False, "severity": "safe"},
                                },
                            ),
                        ],
                        created=1703462735,
                        model="gpt-35-turbo",
                    ),
                )
            self.chunks.append(
                openai.types.chat.ChatCompletionChunk(
                    id="test-123",
                    object="chat.completion.chunk",
                    choices=[
                        openai.types.chat.chat_completion_chunk.Choice(
                            delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(content=None, role=None),
                            index=0,
                            finish_reason="stop",
                            # Only Azure includes content_filter_results
                            content_filter_results={},
                        ),
                    ],
                    created=1703462735,
                    model="gpt-35-turbo",
                ),
            )

        def __aiter__(self):  # noqa: ANN204
            return self

        async def __anext__(self):  # noqa: ANN204
            if self.chunk_index < len(self.chunks):
                next_chunk = self.chunks[self.chunk_index]
                self.chunk_index += 1
                return next_chunk
            else:  # noqa: RET505
                raise StopAsyncIteration

    async def mock_acreate(*args, **kwargs) -> Any:  # noqa: ANN003, ANN002, ARG001, ANN401
        if kwargs.get("stream"):
            return AsyncChatCompletionIterator("The capital of France is Paris.")
        else:  # noqa: RET505
            return openai.types.chat.ChatCompletion(
                object="chat.completion",
                choices=[
                    openai.types.chat.chat_completion.Choice(
                        message=openai.types.chat.chat_completion.ChatCompletionMessage(
                            role="assistant", content="The capital of France is Paris.",
                        ),
                        finish_reason="stop",
                        index=0,
                        logprobs=None,
                    ),
                ],
                id="test-123",
                created=0,
                model="test-model",
                usage=openai.types.completion_usage.CompletionUsage(
                    completion_tokens=7,
                    prompt_tokens=24,
                    total_tokens=31,
                ),
            )

    monkeypatch.setattr("openai.resources.chat.AsyncCompletions.create", mock_acreate)


@pytest.fixture()
def mock_azure_credentials(monkeypatch) -> None :  # noqa: PT004, ANN001
    """Fixture for mocking Azure credentials using monkeypatch."""
    class MockAzureCredential(azure.core.credentials_async.AsyncTokenCredential):
        """Fixture for mocking Azure credentials using monkeypatch."""

    monkeypatch.setattr("azure.identity.aio.DefaultAzureCredential", MockAzureCredential)
    monkeypatch.setattr("azure.identity.aio.ManagedIdentityCredential", MockAzureCredential)
