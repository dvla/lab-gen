from __future__ import annotations

import json

from pathlib import Path

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    messages_from_dict,
    messages_to_dict,
)
from loguru import logger

from lab_gen.datatypes.metadata import ConversationMetadata
from lab_gen.services.chat_history import chat_message
from lab_gen.settings import settings


class FileChatHistory(BaseChatMessageHistory):
    """File-based storage."""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        metadata: ConversationMetadata,
    ) -> None:
        """Initialize FileChatHistory with session details and file path.

        Args:
            session_id: Unique identifier for the conversation.
            user_id: Identifier for the user involved in the conversation.
            metadata: Metadata associated with the conversation.
        """
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata
        self.messages = []  # Initialize a basemessage list for compatibility

        # Determine if the provided file path is a directory or a full path
        path_obj = settings.chat_history_dir
        self.file_path = path_obj / f"{session_id}.json"

        self.load_messages()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(
            f"FileChatHistory in use for session {session_id} with user {user_id}. Messages saved to {self.file_path}",
        )



    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the history and save it to the file."""
        self.messages.append(message)  # Add to in-memory list.
        self.upsert_messages()  # Save message to file

    def upsert_messages(self) -> None:
        """Save or update the chat history and metadata in the file."""
        # Check if the file path is initialized
        if not self.file_path:
            msg = "File path not initialized"
            raise ValueError(msg)
        # Prepare the data to be saved
        data = {
            "id": self.session_id,
            "user_id": self.user_id,
            "metadata": self.metadata.model_dump(mode="json") if self.metadata else {},
            "messages": messages_to_dict(self.messages),
        }
        # Save or update the file with the data
        try:
            with Path.open(self.file_path, "w") as f:
                json.dump(data, f, indent=4)  # Use json.dump to write data in a readable format
            logger.debug(f"Chat history and metadata updated for session {self.session_id}")
        except OSError as e:
            logger.error(f"Failed to write data to file: {e}")
            raise

    def load_messages(self) -> list[BaseMessage]:
        """Load messages, metadata, and IDs from the file."""
        self.messages = []  # Initialize an empty list for messages

        if not self.file_path.exists():
            return self.messages

        try:
            with Path.open(self.file_path) as f:
                data = json.load(f)
                if "messages" in data:
                    self.messages = messages_from_dict(data["messages"])
                if "metadata" in data:
                    self.metadata = ConversationMetadata.model_validate(data["metadata"])

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error loading messages: {e}")

        return self.messages

    def delete(self, num_entries: int) -> None:
        """Delete a specific number of message entry pairs."""
        if not self.file_path.exists():
            raise ValueError("File not exist")  # noqa: EM101, TRY003

        logger.debug(f"Deleting {num_entries} entry pairs from conversation {self.session_id}")

        # Update messages using calculate_messages
        self.messages = chat_message.calculate_messages(self.messages, num_entries)

         # Update the file with the remaining messages
        self.upsert_messages()

    def clear(self) -> None:
        """Clear messages from the history and delete the file."""
        self.messages.clear()
        try:
            # Delete the file if it exists
            if self.file_path.exists():
                self.file_path.unlink()
            else:
                logger.warning(f"Chat history file not found for session {self.session_id}, nothing to delete.")
        except OSError as e:
            logger.error(f"Failed to delete chat file: {e}")
            raise
