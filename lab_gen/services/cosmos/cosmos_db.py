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

from lab_gen.datatypes.errors import InvalidParamsError, NoConversationError
from lab_gen.datatypes.messages import MESSAGE_TYPE_AI
from lab_gen.datatypes.metadata import ConversationMetadata
from lab_gen.services.cosmos.lifetime import CONTAINER_NAME, DATABASE_NAME


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

    @staticmethod
    def calculate_messages(messages: list[BaseMessage], num_entries: int) -> list[BaseMessage]:
        """
        Calculate the messages to delete based on the given criteria.

        Args:
            messages (list[BaseMessage]): The list of messages to process.
            num_entries (int): The number of message sets to delete.

        Raises:
            NoConversationError: If no messages are found.
            InvalidParamsError: If the number of message sets to delete is greater than the amount of messages in the
            conversation, or if the amount of messages to delete is less than or equal to 0, or if the messages list
            does not consist of an even number of 'human' and 'ai' messages.

        Returns:
            list[BaseMessage]: The updated list of messages after processing.
        """
        if not messages:
            msg = "No messages found"
            raise NoConversationError(msg)

        total_entries_to_delete = num_entries * 2  # since one set is "human" + "ai"

        if total_entries_to_delete > len(messages):
            msg = "Amount of message sets to delete is greater than the amount of messages in the conversation"
            raise InvalidParamsError(msg)

        if num_entries <= 0:
            msg = "Amount of messages to delete must be greater than 0"
            raise InvalidParamsError(msg)

        if len(messages) % 2 != 0:
            msg = "The messages list does not consist of an even number of 'human' and 'ai' messages"
            raise InvalidParamsError(msg)

        if messages[-1].type == MESSAGE_TYPE_AI:
            messages = messages[:-total_entries_to_delete]

        return messages

    def delete(self, num_entries: int) -> None:
        """Delete a message from the memory."""
        if not self._container:
            msg = "Container not initialized"
            raise InvalidParamsError(msg)

        logger.debug(f"Deleting {num_entries} entry pairs from conversation {self.session_id}")
        message_length = len(self.messages)
        self.messages = self.calculate_messages(self.messages, num_entries)
        if len(self.messages) != message_length:
            self.upsert_messages()
