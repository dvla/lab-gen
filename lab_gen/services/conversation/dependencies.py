from fastapi import Request

from lab_gen.services.conversation.conversation import ConversationService


def conversation_provider(request: Request) -> ConversationService:  # pragma: no cover
    """Return the ConversationService instance from the request state."""
    return request.app.state.conversation_provider
