import json
import re

from pathlib import Path

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langsmith import expect, unit
from loguru import logger
from starlette import status

from lab_gen.datatypes.models import (
    ModelProvider,
    ModelVariant,
)


TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "data/call_transcripts/"
provider = ModelProvider.VERTEX
variant = ModelVariant.ADVANCED


def pytest_generate_tests(metafunc) -> None:  # noqa: ANN001
    """Define the pytest_generate_tests hook.

    Generates test cases based on the test data directory.

    Parameters:
    - metafunc: The pytest metafunc object.
    """
    expectlist = list(TEST_DATA_DIR.rglob("expect*"))
    params = []
    for expect_file in expectlist:
        script_file = str(expect_file.name).replace("expect", "script").replace(".json", ".csv")
        params.append((script_file, json.load(Path.open(expect_file)), provider.name, variant.name))
    if "input_file" in metafunc.fixturenames:
        metafunc.parametrize("input_file,expected,provider,variant", params)


@pytest.mark.anyio()
@unit(output_keys=["expected"])
def test_call_transcript(fastapi_app: FastAPI, input_file: str, expected: dict, provider: str, variant: str) -> None:
    """
    Test the call transcript endpoint.

    Parameters:
    - fastapi_app (FastAPI): The FastAPI application instance.
    """
    with TestClient(fastapi_app) as test_client:
        url = fastapi_app.url_path_for("call_handler")
        payload = {
            "provider": provider,
            "variant": variant,
            "variables": {"input":  re.escape(Path.open(TEST_DATA_DIR / input_file).read())},
        }

        # Call the endpoint
        response = test_client.post(
            url, json=payload, headers={"Authorization": "pytest_key", "x-business-user": "bob.smith"},
        )
        assert response.status_code == status.HTTP_200_OK
        call = response.json()
        logger.warning(call)
        expect.value(call["startTime"]).to_equal(expected["startTime"])
        expect.value(call["endTime"]).to_equal(expected["endTime"])
        expect.value(call["sentiment"].lower()).to_equal(expected["sentiment"])
        expect.value(call["category"]).to_contain(expected["category"][0])
        expect.value(call["participants"]).to_contain(expected["participants"][0])
