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

from app.api.dependencies import get_conversation_service

from app.services.llm.llm_io import LLMConversationMessage, LLMConversationRequest

from app.schemas.requests import ConversationRequest

from app.schemas.responses import ConversationResponse, Turn


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


@app.post("/conversation", response_model=ConversationResponse)
async def conversation(
    request: ConversationRequest,
    bg: BackgroundTasks,
    _auth: bool = Depends(require_api_key),
    conversation_service=Depends(get_conversation_service),
):

    if not request.message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing message field."
        )

    conversation_id = request.conversation_id
    input_message = LLMConversationMessage(role="user", content=request.message)

    print(f"Conversation_id: {conversation_id}")
    print(f"User message: {input_message}")

    if not conversation_id:
        print("Starting conversation")
        input_message.role = "system"
        conversation_id = await conversation_service.start_conversation(input_message)

    response, llm_formated_response = await conversation_service.continue_conversation(
        conversation_id, input_message
    )

    bg.add_task(
        conversation_service.persist_conversation,
        conversation_id,
        input_message,
        llm_formated_response,
    )

    result = ConversationResponse(
        conversation_id=conversation_id, message=response["message"]
    )

    return result
