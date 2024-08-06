import json

import pytest

from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import ValidationError
from starlette import status

from lab_gen.datatypes.models import AzureModelConfig, BedrockModelConfig, HuggingfaceModelConfig


def test_azure_load() -> None:
    """Test the loading of a JSON configuration."""
    raw_config = """{"AZURE_OPENAI_API_KEY": "Kong", "AZURE_OPENAI_ENDPOINT": "James",
                     "AZURE_OPENAI_API_VERSION": "2022-12-01"}"""
    conf_dict = json.loads(raw_config)
    conf = AzureModelConfig(**conf_dict)
    assert conf.endpoint == "James"
    assert conf.api_key == "Kong"


def test_bedrock_load() -> None:
    """Test the loading of a JSON configuration."""
    raw_config = """{"AWS_REGION": "King", "AWS_ACCESS_KEY_ID": "Paul",
                     "AWS_SECRET_ACCESS_KEY": "01"}"""
    conf_dict = json.loads(raw_config)
    conf = BedrockModelConfig(**conf_dict)
    assert conf.aws_access_key_id == "Paul"
    assert conf.region_name == "King"

def test_huggingface_load() -> None:
    """Test the loading of a JSON configuration."""
    raw_config = """{"HF_REPO_ID": "Kong",
                     "HF_TOKEN": "201"}"""
    conf_dict = json.loads(raw_config)
    conf = HuggingfaceModelConfig(**conf_dict)
    assert conf.repo_id == "Kong"
    assert conf.access_token == "201"  # noqa: S105

def test_json_validation() -> None:
    """Test the loading of a invalid JSON."""
    raw_config = """{"MISSING_KEY": "Kong", "AZURE_OPENAI_ENDPOINT": "James",
                    "AZURE_OPENAI_API_VERSION": "2022-12-01"}"""
    conf_dict = json.loads(raw_config)
    with pytest.raises(ValidationError, match=r".*AZURE_OPENAI_API_KEY.*"):
        AzureModelConfig(**conf_dict)


@pytest.mark.anyio()
async def test_read_models(client: AsyncClient, fastapi_app: FastAPI) -> None:
    """
    Checks the read_models endpoint.

    :param client: client for the app.
    :param fastapi_app: current FastAPI application.
    """
    url = fastapi_app.url_path_for("read_models")
    response = await client.get(url)
    assert response.status_code == status.HTTP_200_OK
    res = response.json()
    assert res[0]["location"] == "UK"
    assert res[0]["provider"] == "AZURE"
