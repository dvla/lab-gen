from __future__ import annotations

from typing import TYPE_CHECKING

from azure.cosmos.exceptions import CosmosHttpResponseError
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    messages_from_dict,
    messages_to_dict,
)
from loguru import logger

from lab_gen.datatypes.errors import InvalidParamsError
from lab_gen.datatypes.metadata import ConversationMetadata
from lab_gen.services.chat_history import chat_message
from lab_gen.services.chat_history.lifetime import CONTAINER_NAME, DATABASE_NAME


if TYPE_CHECKING:
    from azure.cosmos import CosmosClient


class CosmosDBChatMessageHistory(BaseChatMessageHistory):
    """Chat message history backed by Azure CosmosDB."""

    def __init__(
        self,
        cosmos_client: CosmosClient,
        session_id: str,
        user_id: str,
        metadata: ConversationMetadata,
    ) -> None:
        """Initializes a new instance of the CosmosDBChatMessageHistory class."""
        self._client = cosmos_client
        self.session_id = session_id
        self.user_id = user_id.lower()
        self.metadata = metadata
        self.messages: list[BaseMessage] = []

        if (cosmos_client):
            database = cosmos_client.get_database_client(DATABASE_NAME)
            self._container = database.get_container_client(CONTAINER_NAME)
            self.load_messages()

    def load_messages(self) -> None:
        """Retrieve the messages from Cosmos."""
        if not self._container:
            msg = "Container not initialized"
            raise ValueError(msg)
        try:
            item = self._container.read_item(
                item=self.session_id, partition_key=self.user_id,
            )
        except CosmosHttpResponseError:
            logger.debug(f"No conversation found for {self.session_id}")
            return
        if "messages" in item and len(item["messages"]) > 0:
            self.messages = messages_from_dict(item["messages"])
        if "metadata" in item:
            self.metadata = ConversationMetadata.model_validate(item["metadata"])

    def add_message(self, message: BaseMessage) -> None:
        """Add a self-created message to the store."""
        self.messages.append(message)
        self.upsert_messages()

    def upsert_messages(self) -> None:
        """Update the cosmosdb item."""
        if not self._container:
            msg = "Container not initialized"
            raise ValueError(msg)
        self._container.upsert_item(
            body={
                "id": self.session_id,
                "user_id": self.user_id,
                "metadata": self.metadata.model_dump(mode="json"),
                "messages": messages_to_dict(self.messages),
            },
        )

    def clear(self) -> None:
        """Clear session memory from this memory and cosmos."""
        self.messages = []
        if self._container:
            logger.debug(f"Deleting conversation {self.session_id}")
            self._container.delete_item(
                item=self.session_id, partition_key=self.user_id,
            )

    def delete(self, num_entries: int) -> None:
        """Delete a message from the memory."""
        if not self._container:
            msg = "Container not initialized"
            raise InvalidParamsError(msg)

        logger.debug(f"Deleting {num_entries} entry pairs from conversation {self.session_id}")
        message_length = len(self.messages)
        self.messages = chat_message.calculate_messages(self.messages, num_entries)
        if len(self.messages) != message_length:
            self.upsert_messages()
