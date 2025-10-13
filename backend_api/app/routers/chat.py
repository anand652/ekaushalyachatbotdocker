#backend_api/app/routers/chat.py

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from .. import schemas, security
from ..chat import get_chatbot_response, get_chatbot_response_stream

router = APIRouter()

@router.post("/query", response_model=schemas.ChatResponse)
def handle_chat_query(
    request: schemas.ChatQuery,
    current_user: dict = Depends(security.get_current_regular_user)
):
    """
    Handles a user's chat query.
    - Requires a valid JWT from any logged-in user.
    - Extracts company_id from the token to ensure data isolation.
    """
    company_id = current_user["company_id"]
    answer = get_chatbot_response(query=request.query, company_id=company_id)
    return schemas.ChatResponse(answer=answer)

@router.post("/query_stream")
def handle_chat_query_stream(
    request: schemas.ChatQuery,
    current_user: dict = Depends(security.get_current_regular_user)
):
    """
    Handles a user's chat query with a streaming response.
    - Requires a valid JWT from any logged-in user.
    - Extracts company_id from the token to ensure data isolation.
    """
    company_id = current_user["company_id"]
    # Get the streaming generator from the chat logic
    generator = get_chatbot_response_stream(query=request.query, company_id=company_id)
    # Return a StreamingResponse from FastAPI
    return StreamingResponse(generator, media_type="text/plain")