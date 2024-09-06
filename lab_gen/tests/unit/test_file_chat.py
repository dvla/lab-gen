import json
import uuid

from pathlib import Path

import pytest

from langchain_core.messages import HumanMessage

from lab_gen.datatypes.metadata import ConversationMetadata
from lab_gen.datatypes.models import ModelFamily, ModelProvider, ModelVariant
from lab_gen.services.chat_history.file_chat import FileChatHistory
from lab_gen.settings import TEMP_DIR, settings


# Define constants for test messages
TWO_MESSAGES = 2
FOUR_MESSAGES = 4


@pytest.fixture(scope="session", autouse=True)
def _before_all() -> None:
    settings.chat_history_dir = TEMP_DIR

@pytest.fixture(scope="session", autouse=True)
def chat_history():  # noqa: ANN201
    """Fixture to create an instance of FileChatHistory with real metadata."""
    session_id = str(uuid.uuid4())
    user_id = "test_user"

    # Create metadata with actual values
    metadata = ConversationMetadata(
        provider=ModelProvider.AZURE,  # Use actual enum value
        variant=ModelVariant.GENERAL,  # Use actual enum value
        family=ModelFamily.GPT,  # Use actual enum value
        modelKey="fake_model_key",  # Use a fake key to ensure no sensitive information
        business_user="test_business_user",
    )

    return FileChatHistory(session_id, user_id, metadata)  # type: ignore  # noqa: PGH003


def test_add_real_message(chat_history) -> None:  # noqa: ANN001
    """Test adding a real HumanMessage to the chat history."""
    message = HumanMessage(content="This is a real message.")
    chat_history.add_message(message)

    assert len(chat_history.messages) == 1
    assert chat_history.messages[0].content == "This is a real message."
    assert chat_history.messages[0].type == "human"


def test_upsert_messages(chat_history) -> None:  # noqa: ANN001
    """Test saving messages to the file."""
    message = HumanMessage(content="This is another real message.")
    chat_history.add_message(message)

    # Check if the file is created
    assert chat_history.file_path.exists()

    # Load the file and verify the contents
    with chat_history.file_path.open() as f:
        data = json.load(f)

    assert data["user_id"] == "test_user"
    assert "messages" in data


def test_clear(chat_history) -> None:  # noqa: ANN001
    """Test clearing the chat history and deleting the file."""
    message = HumanMessage(content="Message to be cleared.")
    chat_history.add_message(message)

    # Ensure the file exists
    assert chat_history.file_path.exists()

    # Clear the history and delete the file
    chat_history.clear()

    assert len(chat_history.messages) == 0
    assert not chat_history.file_path.exists()


def test_load_messages_existing_file(chat_history) -> None:  # noqa: ANN001
    """Test loading messages from an existing file with valid data."""
    # Add and save a message
    message = HumanMessage(content="This is a real message for loading.")
    chat_history.add_message(message)
    chat_history.upsert_messages()  # Ensure the message is saved

    # Create a new FileChatHistory instance to test loading
    new_chat_history = FileChatHistory(chat_history.session_id, chat_history.user_id, chat_history.metadata)
    new_chat_history.load_messages()

    # Verify the loaded message
    assert len(new_chat_history.messages) == 1
    assert new_chat_history.messages[0].content == "This is a real message for loading."
    assert new_chat_history.messages[0].type == "human"


def test_load_non_existent_file(chat_history) -> None:  # noqa: ANN001
    """Test loading from a non-existent file."""
    # Manually set file path to a non-existent file
    chat_history.file_path = Path("non_existent_file.json")

    loaded_messages = chat_history.load_messages()
    assert loaded_messages == []
