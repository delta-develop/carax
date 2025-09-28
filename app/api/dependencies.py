from app.services.conversation.conversation_service import ConversationService
from fastapi import Request


def get_conversation_service(request: Request) -> ConversationService:
    """Fetch the conversation service from the app state.

    Args:
        request: Incoming request used to access the app state.

    Returns:
        ConversationService: Bound service instance.
    """
    return request.app.state.conversation_service
