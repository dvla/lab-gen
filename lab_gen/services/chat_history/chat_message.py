from __future__ import annotations

from typing import TYPE_CHECKING

from lab_gen.datatypes.errors import InvalidParamsError, NoConversationError
from lab_gen.datatypes.messages import MESSAGE_TYPE_AI


if TYPE_CHECKING:
        from langchain_core.messages import BaseMessage


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
