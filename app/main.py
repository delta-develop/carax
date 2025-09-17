import os
import dotenv
from fastapi import (
    APIRouter,
    FastAPI,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    Depends,
    status,
    BackgroundTasks,
)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Any, Optional

import openai
from app.services.memory.cognitive_orchestrator import CognitiveOrchestrator
from app.services.storage.relational_storage import RelationalStorage
from app.services.storage.cache_storage import CacheStorage
from app.utils.sanitization import sanitize_message
from app.utils.message_adapter import (
    format_conversation,
    message_from_user_input,
    message_from_llm_output,
)

from app.services.llm.openai_client import OpenAIClient
import json
from app.services.memory.working_memory import WorkingMemory
from app.prompts.build_prompt import (
    build_conversation_prompt,
    build_new_conversation_prompt,
)

dotenv.load_dotenv()
security = HTTPBearer()
API_KEY = os.getenv("API_KEY", "dev-leonardo-key")
app = FastAPI()
router = APIRouter()
app.include_router(router)

# Initialize cache storage for debug/dev utilities
relational_storage = RelationalStorage()
llm = OpenAIClient()
working_memory = WorkingMemory()


async def require_api_key(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> bool:
    if creds is None or creds.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token"
        )

    return True


@app.post("/debug/migrate-memory")
async def migrate_memory_endpoint(user_id: str):
    """
    Triggers the persistence of memory data to long-term storage for the given user ID.

    Args:
        user_id (str): The user's phone number identifier.

    Returns:
        dict: Result message or error.
    """
    try:
        orchestrator = await CognitiveOrchestrator.from_defaults()
        await orchestrator.persist_conversation_closure(user_id)
        return {"message": f"Memoria migrada correctamente para el usuario {user_id}"}
    except Exception as e:
        return {"error": str(e)}


# Author information endpoint
@app.get("/author")
async def get_author(_auth: bool = Depends(require_api_key)):
    """
    Returns author metadata for the project.

    Returns:
        dict: Author information.
    """
    return {
        "name": "Leonardo HG",
        "location": "Ciudad de México",
        "role": "Backend Developer",
        "project": "Tech Challenge - Kopi (Carax)",
    }


@app.post("/chat")
async def conversation(
    request: Request, bg: BackgroundTasks, _auth: bool = Depends(require_api_key)
):
    data = await request.json()

    conversation_id = data.get("conversation_id")
    message = data.get("message")

    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing message field."
        )

    user_message = message_from_user_input(message)

    if not conversation_id:
        new_conversation_prompt = build_new_conversation_prompt(user_message)
        llm_response = await llm.generate_response(
            [{"role": "user", "content": new_conversation_prompt}]
        )
        llm_response_dict = json.loads(llm_response)
        topic_and_stance = {
            "topic": llm_response_dict["topic"],
            "stance": llm_response_dict["stance"],
        }
        conversation_id = await relational_storage.save(topic_and_stance)

        await working_memory.store_in_memory(
            f"{conversation_id}:meta", topic_and_stance
        )

        llm_response_dict.update({"conversation_id": conversation_id})

        return llm_response_dict

    redis_stored_messages = await working_memory.retrieve_from_memory(conversation_id)
    topic_and_stance = await working_memory.retrieve_from_memory(
        f"{conversation_id}:meta"
    )
    messages_summary = await relational_storage.get(
        filters={"id": conversation_id, "table": "summary"}
    )

    conversation_prompt = build_conversation_prompt(
        topic_and_stance, redis_stored_messages, messages_summary, user_message
    )

    llm_response = await llm.generate_response(
        [{"role": "user", "content": conversation_prompt}]
    )

    llm_formated_response = message_from_llm_output(llm_response)

    async def _persist(user_message, llm_formated_response):

        data = {
            "user_message": user_message,
            "bot_message": llm_formated_response,
        }

        await working_memory.store_in_memory(conversation_id, data)

        data["conversation_id"] = conversation_id

        await relational_storage.save(data)

    bg.add_task(_persist, user_message, llm_formated_response)

    messages = redis_stored_messages or []
    messages.append(user_message)
    messages.append(llm_formated_response)

    response = {"conversation_id": conversation_id, "message": messages[-5:]}

    return response
