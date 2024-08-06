import pytest

from langchain_core.messages import AIMessage, HumanMessage

from lab_gen.datatypes.errors import InvalidParamsError, NoConversationError
from lab_gen.services.cosmos.cosmos_db import CosmosDBChatMessageHistory


def test_calculate_messages_deletes_correct_number_of_sets() -> None:
    """Test case for checking if the correct number of message sets are deleted."""
    messages = [HumanMessage(content=["Hello"]), AIMessage(content=["I am a bot"])] * 3
    num_entries = 2
    expected_length = 2  # 3 pairs initially, 2 pairs to be deleted, 1 pair remains

    updated_messages = CosmosDBChatMessageHistory.calculate_messages(messages, num_entries)

    assert len(updated_messages) == expected_length


def test_error_is_raised_when_deleting_more_than_available() -> None:
    """Asynchronous test for calculating message deletion when attempting to delete more sets than available."""
    messages = [HumanMessage(content=["Hello"]), AIMessage(content=["I am a bot"])] * 2
    num_entries = 3  # Attempt to delete 3 sets from a list containing only 2 sets

    with pytest.raises(InvalidParamsError) as excinfo:
        CosmosDBChatMessageHistory.calculate_messages(messages, num_entries)

    assert "greater than the amount of messages" in str(excinfo.value)

def test_error_is_raised_when_num_entries_equals_zero_or_negative_numbers() -> None:
    """Test case for calculating messages with zero or negative entries."""
    messages = [HumanMessage(content=["Hello"]), AIMessage(content=["I am a bot"])]
    num_entries = 0

    with pytest.raises(InvalidParamsError) as excinfo:
        CosmosDBChatMessageHistory.calculate_messages(messages, num_entries)

    assert "must be greater than 0" in str(excinfo.value)

def test_error_raised_when_list_of_messages_is_empty() -> None:
    """A test case for the function calculate_messages with an empty list of messages."""
    messages = []
    num_entries = 1

    with pytest.raises(NoConversationError) as excinfo:
        CosmosDBChatMessageHistory.calculate_messages(messages, num_entries)

    assert "No messages found" in str(excinfo.value)

def test_error_raised_when_odd_number_of_messages() -> None:
    """Test the calculate_messages function with an odd number of messages."""
    messages = [
        HumanMessage(content=["Hello"]),
        AIMessage(content=["I am a bot"]),
        HumanMessage(content=["Another message"]),
    ]
    num_entries = 1

    with pytest.raises(InvalidParamsError) as excinfo:
        CosmosDBChatMessageHistory.calculate_messages(messages, num_entries)

    assert "even number of 'human' and 'ai' messages" in str(excinfo.value)

def test_calculate_messages_deletes_all_messages() -> None:
    """Function to test the calculate_messages method with the goal of deleting all sets of messages."""
    messages = [
        HumanMessage(content=["Hello"]),
        AIMessage(content=["I am a bot"]),
        HumanMessage(content=["Another message"]),
        AIMessage(content=["Another response"]),
    ]
    num_entries = 2  # All sets should be deleted

    updated_messages = CosmosDBChatMessageHistory.calculate_messages(messages, num_entries)
    assert updated_messages == []
