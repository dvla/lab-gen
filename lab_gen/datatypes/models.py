from enum import Enum

from pydantic import BaseModel, Field


class ModelVariant(Enum):
    """Represents different model variants."""

    GENERAL = "GENERAL"
    ADVANCED = "ADVANCED"
    MULTIMODAL = "MULTIMODAL"
    EXPERIMENTAL = "EXPERIMENTAL"

class ModelProvider(Enum):
    """Represents different model providers."""

    AZURE = "AZURE"
    BEDROCK = "BEDROCK"
    VERTEX = "VERTEX"
    HUGGINGFACE = "HUGGINGFACE"

class ModelFamily(Enum):
    """Represents the different model families."""
    GPT = "GPT"
    CLAUDE = "CLAUDE"
    GEMINI = "GEMINI"
    MIXTRAL = "MIXTRAL"
    UNSPECIFIED = "UNSPECIFIED"


class Model(BaseModel):
    """
    Represents a model definition.

    Attributes:
        provider (ModelProvider): The model providers.
        variant (ModelVariant): The variants of the model.
        family (ModelFamily): The family of the model.
        description (str): The description of the model.
        location (str):  The geographic location where the model is running.
    """

    provider: ModelProvider
    variant: ModelVariant
    family: ModelFamily = Field(default=ModelFamily.UNSPECIFIED)
    description: str | None = None
    location: str
    identifier: str = Field(exclude=True)
    config: dict[str, str] | None = Field(None, exclude=True)


class AzureModelConfig(BaseModel):
    """Represents an Azure model config."""

    endpoint: str = Field(alias="AZURE_OPENAI_ENDPOINT")
    api_key: str = Field(alias="AZURE_OPENAI_API_KEY")
    api_version: str = Field(alias="AZURE_OPENAI_API_VERSION")


class BedrockModelConfig(BaseModel):
    """Represents a model config for AWS Bedrock runtime."""

    region_name: str = Field(alias="AWS_REGION")
    aws_access_key_id: str = Field(alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(alias="AWS_SECRET_ACCESS_KEY")

class HuggingfaceModelConfig(BaseModel):
    """Represents a model config for Huggingface."""
    repo_id: str = Field(alias="HF_REPO_ID")
    access_token: str = Field(alias="HF_TOKEN")
