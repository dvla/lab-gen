# DVLA Emerging Tech Lab Generative AI

## Getting Started

## Prerequisites
- Python 3.11
- `pip install poetry`
- `poetry install --with=dev,test`

### Quick Start

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/dvla/lab-gen)

[![Open in VS Code Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/dvla/lab-gen)

To run the project use this set of commands:

Setup the `.env` file:
```bash
cp example.env .env
echo 'LAB_GEN_SESSION_STORE_URI=https://my-store.documents.azure.com:443/'  >> .env
echo 'LAB_GEN_SESSION_STORE_KEY=0177PWaDjWhceFttEK4Q=='  >> .env
```

Setup your models config:
 `cp -r example_secrets secrets`.
 Edit the `AZURE_MODELS` file in `./secrets`.

Run the application:
```bash
poetry run python -m lab_gen
```

This will start the server on the configured host.

You can find swagger documentation at `/api/docs`.

A simple test request is:
```
curl -X 'POST' \
  'http://127.0.0.1:8081/api/conversations' \
  -H 'accept: application/json' \
  -H 'x-business-user: king.kong' \
  -H 'Authorization: 1234' \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "What is the DVLA?"
}'
```

## Project structure

```bash
$ tree "lab_gen"
lab_gen
├── conftest.py  # Fixtures for all tests.
├── __main__.py  # Startup script. Starts uvicorn.
├── services  # Package for different external services such as openai or cosmosdb etc.
├── settings.py  # Main configuration settings for project.
├── static  # Static content.
├── tests  # Tests for project.
└── web  # Package contains web server. Handlers, startup config.
    ├── api  # Package with all handlers.
    │   └── router.py  # Main router.
    ├── application.py  # FastAPI application configuration.
    └── lifetime.py  # Contains actions to perform on startup and shutdown.
```

## Configuration

This application can be configured with environment variables.

You can create `.env` file in the root directory and place all
environment variables here.

All environment variables should start with "LAB_GEN_" prefix.

For example if you see in your "lab_gen/settings.py" a variable named like
`random_parameter`, you should provide the "LAB_GEN_RANDOM_PARAMETER"
variable to configure the value. This behaviour can be changed by overriding `env_prefix` property
in `lab_gen.settings.Settings.Config`.

An example of .env file:
```bash
LAB_GEN_RELOAD="True"
LAB_GEN_PORT="8000"
LAB_GEN_ENVIRONMENT="myname"
LAB_GEN_SESSION_STORE_URI=https://my-store.documents.azure.com:443/
LAB_GEN_SESSION_STORE_KEY=0177PWaDjWhceFttEK4Q==
LAB_GEN_SESSION_STORE_TTL=172800
AZURE_APP_API_KEY=1234
AZURE_MODELS=[{"provider": "AZURE","variant": "GENERAL","identifier": "gpt-35-1106","description": "OpenAI GPT-3.5 Turbo powered","location":"UK"},{"provider": "AZURE","variant": "ADVANCED","identifier": "gpt-4-1106","description": "OpenAI GPT-4","location":"UK"}]
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=99x99999-9xxx-9999-x9x9-9999999x999x;IngestionEndpoint=https://example.in.applicationinsights.azure.com/;LiveEndpoint=https://example.livediagnostics.monitor.azure.com/"
LOGURU_LEVEL="INFO"
TIKTOKEN_CACHE_DIR=tiktoken_cache
```

### Model config
The model configuration is a json list and can be specified in any of the following ways:
1. If an `APPCONFIGURATION_CONNECTION_STRING` is specifed then any variables starting with `AZURE` are looked up in Azure App Config.
    e.g. `AZURE_MODELS`.
2. `AZURE_MODELS` can be specified as an enviroment variable on a single line (see example above).
3. A `secrets` folder can be used to set values.  For example, rename the `example_secrets` folder to just `secrets` and the `AZURE_MODELS` file will be used for the model configuration.

### AWS Guardrails

AWS Guardrails can be configured on the Bedrock models by adding the 'guardrailId' and 'guardrailversion' to the config.

An example of a Bedrock config with Guardrails configured:
```bash
["provider": "BEDROCK",
"variant": "ADVANCED",
"family": "CLAUDE",
"identifier": "anthropic.claude-3-sonnet",
"description": "Claude 3 Sonnet",
"location": "Paris",
"config":{"AWS_REGION": "eu-west-3",
          "AWS_ACCESS_KEY_ID": "xxxxx",
          "AWS_SECRET_ACCESS_KEY": "xxxxx",
          "guardrailIdentifier": "ejgbdBFg5TD",
          "guardrailVersion": "DRAFT"}]
```

## Pre-commit

To install pre-commit simply run inside the shell:
```bash
pre-commit install
```

pre-commit is very useful to check your code before publishing it.
It's configured using `.pre-commit-config.yaml` file.

You can read more about pre-commit here: https://pre-commit.com/

## Running tests

For running tests on your local machine.


2. Run the pytest.
```bash
pytest -vv
```

## Langfuse

Langfuse tracks traces of LLM calls. Traces can be view at [Langfuse Cloud](https://cloud.langfuse.com). You need to add the following to ```.env```.

```bash
LANGFUSE_SECRET_KEY="secret-key" # available from langfuse cloud Settings
LANGFUSE_PUBLIC_KEY="public-key" # available from langfuse cloud Settings
LANGFUSE_HOST="langfuse host url" # available from langfuse cloud Settings
```

## License
The MIT License (MIT)

Copyright (c) 2024 DVLA

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
