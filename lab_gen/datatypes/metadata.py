from enum import Enum

from pydantic import BaseModel

from lab_gen.datatypes.models import ModelProvider, ModelVariant


class ContentType(Enum):
    """Enum for content types supported by the File upload."""
    PNG = "image/png"
    JPG = "image/jpeg"

class ConversationMetadata(BaseModel):
    """Model for storing metadata about a conversation.

    Attributes:
    - provider (ModelProvider): The model provider used for the conversation.
    - variant (ModelVariant): The model variant used for the conversation.
    - business_user (str): Business user associated with the conversation.
    """

    provider: ModelProvider
    variant: ModelVariant
    business_user: str
