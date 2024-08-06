import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette import status


@pytest.mark.anyio()
def test_delete_conversation(fastapi_app: FastAPI) -> None:
    """
    Test the delete_conversation endpoint.

    Parameters:
    - fastapi_app (FastAPI): The FastAPI application instance.
    """
    with TestClient(fastapi_app) as test_client:
        url = fastapi_app.url_path_for("end_conversation", conversationId="123")
        response = test_client.delete(url, headers={"Authorization": "pytest_key", "x-business-user": "bob.smith"})
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio()
def test_invalid_start_conversation(fastapi_app: FastAPI) -> None:
    """Test starting a conversation with an invalid prompt ID."""
    with TestClient(fastapi_app) as test_client:
        url = fastapi_app.url_path_for("start_conversation")
        response = test_client.post(url, headers={"Authorization": "pytest_key"}, json={"promptId": "summary"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_start_conversation(fastapi_app: FastAPI, mock_openai_chatcompletion) -> None:  # noqa: ARG001, ANN001
    """Test starting a conversation with an invalid prompt ID."""
    with TestClient(fastapi_app) as test_client:
        url = fastapi_app.url_path_for("start_conversation")
        response = test_client.post(url, headers={"Authorization": "pytest_key", "x-business-user": "123"},
                                    json={"promptId": "summary", "content": "Doesn't really matter"})
        assert response.status_code == status.HTTP_200_OK
        assert response.text == "The capital of France is Paris."


@pytest.mark.anyio()
def test_conversation_history(fastapi_app: FastAPI) -> None:
    """
    Test the conversation history endpoint.

    Parameters:
    - fastapi_app (FastAPI): The FastAPI application instance.
    """
    with TestClient(fastapi_app) as test_client:
        url = fastapi_app.url_path_for("conversation_history", conversationId="123")
        response = test_client.get(
            url,
            headers={"Authorization": "pytest_key", "x-business-user": "bob.smith"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response = test_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
