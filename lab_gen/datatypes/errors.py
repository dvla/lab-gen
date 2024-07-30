class NoConversationError(ValueError):
    """Raises an error when no conversation is found for the given ID.

    Args:
      conversation_id: The ID of the conversation that was not found.
    """

    def __init__(self, conversation_id: str) -> None:
        super().__init__(f"No conversation found for {conversation_id}")


class InvalidParamsError(ValueError):
    """
    Initialize the object with the given parameter.

    Args:
        param (Any): The parameter to initialize the object with.

    Returns:
        None
    """

    def __init__(self, param: str) -> None:
        super().__init__(f"{param}")


class ModelKeyError(ValueError):
    """
    Raises an error when an invalid model key is provided.

    Args:
        param (str): The invalid model key that caused the error.
    """

    def __init__(self, param: str) -> None:
        """
        Initialize the ModelKeyError with the given model key.

        Args:
            param (str): The invalid model key that caused the error.
        """
        super().__init__(f"Invalid model key {param}")
