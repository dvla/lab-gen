import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.prompts.few_shot import FewShotPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from starlette import status

from lab_gen.services.conversation.lifetime import load_prompts


examples, prompts = load_prompts()


def test_template_joke() -> None:
    """Test that the 'joke' prompt template matches the expected template."""
    expected_prompt = PromptTemplate(
        input_variables=["input", "joke_type"],
        template="Tell me a {joke_type} joke about {input}.",
    )
    assert prompts["joke"] == expected_prompt


def test_template_antonyms() -> None:
    """Test that the 'antonyms' prompt template matches the expected template."""
    expected_prompt = FewShotPromptTemplate(
        input_variables=["adjective"],
        prefix="Write antonyms for the following words.",
        example_prompt=PromptTemplate(
            input_variables=["input", "output"],
            template="Input: {input}\nOutput: {output}",
        ),
        examples=[
            {"input": "happy", "output": "sad"},
            {"input": "tall", "output": "short"},
        ],
        suffix="Input: {adjective}\nOutput:",
    )
    assert prompts["antonyms"] == expected_prompt


def test_examples() -> None:
    """Test that the example inputs match expected values."""
    assert examples["joke"] == ["input", "joke_type"]
    assert examples["keywords"] == ["input"]
    assert examples["summary"] == ["input"]


@pytest.mark.anyio()
def test_read_prompts(fastapi_app: FastAPI) -> None:
    """Tests the read_prompts API endpoint."""
    with TestClient(fastapi_app) as test_client:
        url = fastapi_app.url_path_for("read_prompts")
        response = test_client.get(url, headers={"Authorization": "pytest_key"})
        assert response.status_code == status.HTTP_200_OK
        res = response.json()
        assert res["summary"][0] == "input"
        assert res["keywords"][0] == "input"


        response = test_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN



@pytest.mark.anyio()
def test_read_prompts_by_id(fastapi_app: FastAPI) -> None:
    """Tests the read_prompt by Id API endpoint."""
    with TestClient(fastapi_app) as test_client:
        url = fastapi_app.url_path_for("read_prompt", prompt_id="joke")
        response = test_client.get(url, headers={"Authorization": "pytest_key"})
        assert response.status_code == status.HTTP_200_OK
        res = response.json()
        assert res["prompt"] == "Tell me a {joke_type} joke about {input}."

@pytest.mark.anyio()
def test_read_prompts_by_id_not_found(fastapi_app: FastAPI) -> None:
    """Tests the read_prompt by Id API endpoint when the prompt is not found."""
    with TestClient(fastapi_app) as test_client:
        url = fastapi_app.url_path_for("read_prompt", prompt_id="game")
        response = test_client.get(url, headers={"Authorization": "pytest_key"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        res = response.json()
        assert "detail" in res
        assert res["detail"] == "Prompt not found"

@pytest.mark.anyio()
def test_read_prompts_by_id_with_format(fastapi_app: FastAPI) -> None:
    """Tests the read_prompt endpoint with structured format instructions."""
    with TestClient(fastapi_app) as test_client:
        # Test reading the structured_talk_summary prompt
        url = fastapi_app.url_path_for("read_prompt", prompt_id="structured_talk_summary")
        response = test_client.get(url, headers={"Authorization": "pytest_key"})

        # Verify successful response
        assert response.status_code == status.HTTP_200_OK

        # Parse response
        res = response.json()

        # Verify prompt template structure and content
        assert "prompt" in res
        prompt = res["prompt"]

        # Verify schema components are properly included
        assert '"$defs"' in prompt
        assert '"CreativeWork"' in prompt
        assert '"Organisation"' in prompt
        assert '"Person"' in prompt
        assert '"Quotation"' in prompt

        # Verify format instructions
        assert "Here is the output schema:" in prompt
        assert "{input}" in prompt  # Template variable for input text

        # Verify schema requirements
        assert '"required": ["name", "description", "type"]' in prompt  # CreativeWork requirements
        assert '"required": ["name", "description", "brands", "location"]' in prompt  # Organisation requirements
        assert '"required": ["name", "description"]' in prompt  # Person requirements
        assert '"required": ["creator", "text"]' in prompt  # Quotation requirements

@pytest.mark.anyio()
def test_read_prompts_by_id_without_format(fastapi_app: FastAPI) -> None:
    """Tests the read_prompt endpoint to ensure response does not include format-specific components."""
    with TestClient(fastapi_app) as test_client:
        # Test reading a prompt without structured format requirements
        url = fastapi_app.url_path_for("read_prompt", prompt_id="structured_talk_summary")
        response = test_client.get(url, headers={"Authorization": "pytest_key"})

        # Verify successful response
        assert response.status_code == status.HTTP_200_OK

        # Parse response
        res = response.json()

        # Check that the "prompt" field exists
        assert "prompt" in res
        prompt = res["prompt"]

        # Verify the prompt does NOT contain any format-specific instructions or schema definitions
        assert "{format_instructions}" not in prompt
