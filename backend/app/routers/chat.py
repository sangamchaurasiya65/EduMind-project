import json
from typing import List, Generator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db, SessionLocal
from backend.app.models.user import User
from backend.app.models.chat_message import ChatMessage
from backend.app.schemas.chat import (
    ChatRequest,
    ChatMessageItem,
    ChatHistoryResponse,
    ClearChatResponse
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.profile_service import log_user_activity
from backend.app.services.chat_service import (
    check_user_rate_limit,
    extract_relevant_material_chunks,
    stream_gemini_chat_response
)

router = APIRouter(prefix="/chat", tags=["AI Study Assistant"])


@router.post(
    "",
    summary="Submit query to Gemini AI Study Assistant with real-time streaming",
    response_description="Server-Sent Events (SSE) word-by-word streaming stream"
)
def chat_with_gemini(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Directly connects the student to Google Gemini API via official Google Gen AI SDK.
    - Validates student authentication and authorization.
    - Applies per-student rate limiting and 4000-character input validation.
    - Enriches prompt with student's current subject context and uploaded document chunks.
    - Streams response chunks in real-time (SSE format: `data: {"chunk": "..."}\\n\\n`).
    - Persists both user query and generated response to the database for seamless persistence.
    """
    user_id_str = str(current_user.id)
    print(f"\n[API /api/chat] User {user_id_str} asked: \"{req.message[:60]}...\"", flush=True)

    # 1. Rate Limit Enforcement
    allowed, rate_error = check_user_rate_limit(user_id_str)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_error or "Too many requests. Please wait a moment."
        )

    # 2. Extract context from student's uploaded materials (RAG)
    material_chunks = extract_relevant_material_chunks(
        db=db,
        user_id=user_id_str,
        query=req.message,
        subject_code=req.subject_code
    )

    # 3. Persist the user's message in the database
    user_msg_record = ChatMessage(
        user_id=user_id_str,
        role="user",
        content=req.message,
        subject_code=req.subject_code,
        topic=req.topic
    )
    db.add(user_msg_record)
    db.commit()

    # Log study activity for daily streak
    try:
        log_user_activity(
            db=db,
            user_id=user_id_str,
            activity_type="study_session",
            details=f"Asked AI: {req.message[:60]}"
        )
    except Exception:
        pass

    # 4. Generator function for Server-Sent Events (SSE)
    def sse_event_stream() -> Generator[str, None, None]:
        full_ai_response_chunks = []
        
        try:
            for text_chunk in stream_gemini_chat_response(
                message=req.message,
                history=req.history,
                subject_code=req.subject_code,
                subject_name=req.subject_name,
                topic=req.topic,
                material_chunks=material_chunks
            ):
                full_ai_response_chunks.append(text_chunk)
                payload = json.dumps({"chunk": text_chunk})
                yield f"data: {payload}\n\n"
        except Exception as exc:
            err_payload = json.dumps({"chunk": "An error occurred during generation. Please try again."})
            yield f"data: {err_payload}\n\n"
        finally:
            # 5. Persist the complete AI response in database using a fresh session
            complete_response_text = "".join(full_ai_response_chunks).strip()
            if complete_response_text:
                try:
                    with SessionLocal() as save_db:
                        ai_msg_record = ChatMessage(
                            user_id=user_id_str,
                            role="model",
                            content=complete_response_text,
                            subject_code=req.subject_code,
                            topic=req.topic
                        )
                        save_db.add(ai_msg_record)
                        save_db.commit()
                except Exception:
                    pass

            # Notify frontend that the stream is complete
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    summary="Retrieve chat history for the authenticated student"
)
def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns authentic conversation history belonging exclusively to the authenticated learner.
    Ensures multi-tenant data isolation.
    """
    user_id_str = str(current_user.id)
    records = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id_str
    ).order_by(ChatMessage.created_at.asc()).limit(limit).all()

    items = [
        ChatMessageItem(
            id=r.id,
            role=r.role,
            content=r.content,
            subject_code=r.subject_code,
            topic=r.topic,
            created_at=r.created_at
        )
        for r in records
    ]
    return ChatHistoryResponse(messages=items)


@router.delete(
    "/history",
    response_model=ClearChatResponse,
    summary="Clear all conversation messages for the authenticated student"
)
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes all stored chat messages for the current user from the database.
    """
    user_id_str = str(current_user.id)
    deleted_count = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id_str
    ).delete(synchronize_session=False)
    db.commit()

    return ClearChatResponse(
        success=True,
        message="Conversation history cleared successfully.",
        deleted_count=deleted_count
    )

