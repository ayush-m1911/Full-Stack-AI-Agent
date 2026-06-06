"""Chat route — REST + SSE streaming endpoints."""

import uuid
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse, SessionListResponse, Session, ChatMessage
from app.services.agent_service import process_chat, stream_chat, get_session_history

router = APIRouter(prefix="/chat", tags=["Chat"])


_sessions: dict[str, Session] = {}






@router.post("", response_model=ChatResponse, summary="Send a message (REST, non-streaming)")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Full agent pipeline returned as a single JSON response.
    For real-time streaming use POST /api/v1/chat/stream instead.
    """
    session_id = request.session_id or str(uuid.uuid4())
    _register_session(session_id, request.message)

    response = await process_chat(
        session_id=session_id,
        user_message=request.message,
        file_ids=request.file_ids,
        pdf_id=request.pdf_id,
        image_id=request.image_id,
        audio_id=request.audio_id,
    )
    return response






@router.post("/stream", summary="Send a message and stream the agent response (SSE)")
async def chat_stream(request: ChatRequest):
    """
    Streams the agent pipeline as Server-Sent Events (SSE).

    Each event is a JSON line with shape ``StreamEvent``:
    ```
    {"type": "trace",  "trace_step": {...}}
    {"type": "intent", "detected_intent": "summarize"}
    {"type": "token",  "data": "Hello"}
    {"type": "result", "data": "<full response>"}
    {"type": "done"}
    ```
    On ambiguous input:
    ```
    {"type": "followup", "data": "Would you like a summary or sentiment analysis?"}
    {"type": "done"}
    ```
    """
    session_id = request.session_id or str(uuid.uuid4())
    _register_session(session_id, request.message)

    async def event_generator():
        async for line in stream_chat(
            session_id=session_id,
            user_message=request.message,
            file_ids=request.file_ids,
            pdf_id=request.pdf_id,
            image_id=request.image_id,
            audio_id=request.audio_id,
        ):

            yield f"data: {line}\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
        },
    )






def _register_session(session_id: str, message: str) -> None:
    if session_id not in _sessions:
        _sessions[session_id] = Session(
            id=session_id,
            name=message[:40] + ("…" if len(message) > 40 else ""),
        )
    else:
        _sessions[session_id].message_count += 1


@router.get("/sessions", response_model=SessionListResponse, summary="List all sessions")
async def list_sessions() -> SessionListResponse:
    """Returns all active chat sessions."""
    return SessionListResponse(sessions=list(_sessions.values()))


@router.get("/sessions/{session_id}/history", summary="Get message history for a session")
async def session_history(session_id: str):
    """Returns the full message history for a given session."""
    history = get_session_history(session_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or has no messages.",
        )
    return {"session_id": session_id, "messages": history}
