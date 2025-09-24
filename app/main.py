import os
import dotenv
from fastapi import (
    APIRouter,
    FastAPI,
    HTTPException,
    Request,
    Depends,
    status,
    BackgroundTasks,
)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Any, Dict

from app.services.storage.relational_storage import RelationalStorage
from app.utils.message_adapter import (
    message_from_user_input,
)

from app.services.llm.openai_client import OpenAIClient
from app.services.memory.working_memory import WorkingMemory


from contextlib import asynccontextmanager

from app.services.conversation.conversation_service import ConversationService

dotenv.load_dotenv()
security = HTTPBearer()
API_KEY = os.getenv("API_KEY", "dev-leonardo-key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to wire core services.

    Initializes the relational storage, LLM client, and working memory and
    exposes a `ConversationService` through the FastAPI app state.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Controls the startup/shutdown lifecycle.
    """
    relational_storage = RelationalStorage()
    llm = OpenAIClient()
    working_memory = WorkingMemory()

    app.state.conversation_service = ConversationService(
        llm=llm, store=relational_storage, cache=working_memory
    )

    yield


app = FastAPI(lifespan=lifespan)
router = APIRouter()
app.include_router(router)

# Initialize cache storage for debug/dev utilities


def get_conversation_service(request: Request) -> ConversationService:
    """Fetch the conversation service from the app state.

    Args:
        request: Incoming request used to access the app state.

    Returns:
        ConversationService: Bound service instance.
    """
    return request.app.state.conversation_service


async def require_api_key(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> bool:
    """Validate the Bearer token for protected endpoints.

    Args:
        creds: Authorization credentials injected by FastAPI.

    Returns:
        bool: True when the token matches `API_KEY`.

    Raises:
        HTTPException: If credentials are missing or invalid.
    """
    if creds is None or creds.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token"
        )

    return True


# Author information endpoint
@app.get("/author")
async def get_author(_auth: bool = Depends(require_api_key)) -> Dict[str, str]:
    """Return author metadata for the project."""
    return {
        "name": "Leonardo HG",
        "location": "Ciudad de México",
        "role": "Backend Developer",
        "project": "Tech Challenge - Kopi (Carax)",
    }


@app.post("/chat")
async def conversation(
    request: Request,
    bg: BackgroundTasks,
    _auth: bool = Depends(require_api_key),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> Dict[str, Any]:
    """Handle a chat turn and persist it in the background.

    For new conversations (no `conversation_id`), extracts topic and stance.
    For ongoing conversations, composes a debate-aware prompt and returns the
    last 5 messages, scheduling persistence as a background task.

    Args:
        request: Incoming request with JSON containing `message` and optional `conversation_id`.
        bg: FastAPI background task manager to persist the turn asynchronously.
        _auth: Guard ensuring the caller is authorized.
        conversation_service: Injected service orchestrating the conversation.

    Returns:
        dict: Response envelope with either conversation metadata (new) or
            the recent message history (existing).

    Raises:
        HTTPException: If the request payload lacks a `message`.
    """
    data = await request.json()

    conversation_id = data.get("conversation_id")
    message = data.get("message")

    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing message field."
        )

    user_message = message_from_user_input(message)

    if not conversation_id:
        # Si no hay id de conversación, crear la entidad conversación, y ejecutar el comando continue conversation, si hay primer argumento, responder, de no haberlo, dar un primer argumento
        conversation_id = await conversation_service.start_conversation(user_message)

    response, llm_formated_response = await conversation_service.continue_conversation(
        conversation_id, user_message
    )

    bg.add_task(
        conversation_service.persist_conversation,
        conversation_id,
        user_message,
        llm_formated_response,
    )

    return response
