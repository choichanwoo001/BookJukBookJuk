"""책 단위 채팅 API.

세션 워밍업과 SSE 스트리밍 메시지 엔드포인트를 제공한다.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse

from backend.services import book_chat_service

router = APIRouter(tags=["book_chat"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.post("/api/books/{book_id}/chat/session")
async def warmup_session(book_id: str) -> dict[str, Any]:
    """세션을 미리 빌드(또는 캐시 hit 확인)하여 후속 메시지 응답을 빠르게 한다."""
    session = await book_chat_service.get_or_create_session(book_id)
    ctx = getattr(session, "ctx", None)
    return {
        "status": "ready",
        "bookId": book_id,
        "title": getattr(ctx, "title", "") if ctx else "",
        "authors": getattr(ctx, "authors", "") if ctx else "",
    }


@router.post("/api/books/{book_id}/chat/messages")
async def post_message(
    book_id: str,
    payload: dict[str, Any] = Body(..., embed=False),
) -> StreamingResponse:
    """SSE 로 답변 토큰을 스트리밍한다."""
    question = str(payload.get("question") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 필드가 필요합니다.")

    return StreamingResponse(
        book_chat_service.stream_chat(book_id, question),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post("/api/books/{book_id}/chat/reset")
def reset_chat(book_id: str) -> dict[str, Any]:
    """세션 히스토리만 초기화 (KG/벡터 캐시는 유지)."""
    ok = book_chat_service.reset_session(book_id)
    return {"status": "ok" if ok else "noop", "bookId": book_id}
