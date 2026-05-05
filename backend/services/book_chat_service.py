"""책 채팅 세션 캐시 + SSE 스트리밍 서비스.

`ai/book_chat` 패키지의 `ChatSession` 을 book_id 별로 인메모리 LRU 캐시한다.
캐시 미스 시 Supabase `books` 에서 ISBN13/제목/저자를 조회해 즉시 빌드한다.
멀티 프로세스/재시작 무손실은 지원하지 않는다 (단일 워커 가정).
"""
from __future__ import annotations

import asyncio
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, AsyncIterator

from fastapi import HTTPException

from backend.repositories.supabase_repo import must_supabase

# 캐시 설정 ----------------------------------------------------------------
MAX_SESSIONS = 8
SESSION_TTL_SEC = 1800   # 30분
BUILD_TIMEOUT_SEC = 90   # create_session 빌드 타임아웃


@dataclass
class _CacheEntry:
    session: Any              # book_chat.ChatSession
    last_used_ts: float


_SESSION_CACHE: "OrderedDict[str, _CacheEntry]" = OrderedDict()
_BUILD_LOCKS: dict[str, asyncio.Lock] = {}
_CACHE_LOCK = asyncio.Lock()


# 내부 유틸 ----------------------------------------------------------------

def _now() -> float:
    return time.monotonic()


def _evict_expired_locked() -> None:
    """TTL 초과 항목 제거. _CACHE_LOCK 보호 영역에서 호출."""
    cutoff = _now() - SESSION_TTL_SEC
    expired = [bid for bid, entry in _SESSION_CACHE.items() if entry.last_used_ts < cutoff]
    for bid in expired:
        _SESSION_CACHE.pop(bid, None)


def _evict_overflow_locked() -> None:
    """LRU 초과분 제거. _CACHE_LOCK 보호 영역에서 호출."""
    while len(_SESSION_CACHE) > MAX_SESSIONS:
        _SESSION_CACHE.popitem(last=False)


async def _get_build_lock(book_id: str) -> asyncio.Lock:
    async with _CACHE_LOCK:
        lock = _BUILD_LOCKS.get(book_id)
        if lock is None:
            lock = asyncio.Lock()
            _BUILD_LOCKS[book_id] = lock
        return lock


def _fetch_book_meta(book_id: str) -> dict[str, str]:
    """Supabase `books` 에서 isbn13/title/authors 조회 (id == ISBN13 가정)."""
    sb = must_supabase()
    res = (
        sb.table("books")
        .select("id, title, authors")
        .eq("id", book_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    row = rows[0]
    return {
        "isbn13": str(row.get("id") or "").strip(),
        "title": str(row.get("title") or "").strip(),
        "authors": str(row.get("authors") or "").strip(),
    }


async def _build_session(book_id: str) -> Any:
    """`book_chat.create_session` 으로 새 세션을 빌드한다."""
    try:
        from book_chat import create_session
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"book_chat 패키지 로드 실패: {exc}",
        ) from exc

    meta = _fetch_book_meta(book_id)
    isbn13 = meta["isbn13"]
    title = meta["title"]
    authors = meta["authors"]

    primary_author = authors.split(",")[0].strip() if authors else ""

    try:
        return await asyncio.wait_for(
            create_session(
                isbn13=isbn13 or None,
                title=title or None,
                author=primary_author or None,
            ),
            timeout=BUILD_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=f"세션 빌드 타임아웃({BUILD_TIMEOUT_SEC}s)",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"세션 빌드 실패: {exc!s}",
        ) from exc


# 공개 API ------------------------------------------------------------------

async def get_or_create_session(book_id: str) -> Any:
    """캐시 hit 면 즉시 반환, miss 면 Supabase 조회 + create_session 후 캐시."""
    bid = (book_id or "").strip()
    if not bid:
        raise HTTPException(status_code=400, detail="book_id 가 비어있습니다.")

    async with _CACHE_LOCK:
        _evict_expired_locked()
        entry = _SESSION_CACHE.get(bid)
        if entry is not None:
            entry.last_used_ts = _now()
            _SESSION_CACHE.move_to_end(bid)
            return entry.session

    build_lock = await _get_build_lock(bid)
    async with build_lock:
        # 더블 체크 (대기 중 다른 코루틴이 이미 빌드했을 수 있음)
        async with _CACHE_LOCK:
            entry = _SESSION_CACHE.get(bid)
            if entry is not None:
                entry.last_used_ts = _now()
                _SESSION_CACHE.move_to_end(bid)
                return entry.session

        session = await _build_session(bid)

        async with _CACHE_LOCK:
            _SESSION_CACHE[bid] = _CacheEntry(session=session, last_used_ts=_now())
            _SESSION_CACHE.move_to_end(bid)
            _evict_overflow_locked()

    return session


def reset_session(book_id: str) -> bool:
    """세션 히스토리만 초기화 (KG/벡터 캐시는 유지). 세션이 없으면 False."""
    bid = (book_id or "").strip()
    entry = _SESSION_CACHE.get(bid)
    if entry is None:
        return False
    try:
        entry.session.reset_history()
    except Exception:
        return False
    return True


def _sse_event(payload: dict[str, Any], event: str | None = None) -> bytes:
    """SSE 라인을 직렬화한다."""
    lines: list[str] = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(payload, ensure_ascii=False)}")
    lines.append("")  # 종결 빈 라인
    return ("\n".join(lines) + "\n").encode("utf-8")


async def stream_chat(book_id: str, question: str) -> AsyncIterator[bytes]:
    """SSE 바이트 스트림 제너레이터.

    프레임 종류:
      event: ready  data: {"status": "ready"}              세션 준비 완료
      event: delta  data: {"text": "<token>"}              답변 토큰
      event: rejected data: {"text": "..."}                관련성 가드 탈락
      event: done   data: {"text": "<final>"}              종료
      event: error  data: {"detail": "..."}                서버 에러
    """
    q = (question or "").strip()
    if not q:
        yield _sse_event({"detail": "question 이 비어있습니다."}, event="error")
        return

    try:
        session = await get_or_create_session(book_id)
    except HTTPException as exc:
        yield _sse_event({"detail": exc.detail, "status": exc.status_code}, event="error")
        return
    except Exception as exc:  # noqa: BLE001
        yield _sse_event({"detail": f"세션 준비 실패: {exc!s}"}, event="error")
        return

    yield _sse_event({"status": "ready"}, event="ready")

    try:
        async for chunk in session.chat_stream(q):
            ctype = chunk.get("type")
            text = chunk.get("text", "")
            if ctype == "rejected":
                yield _sse_event({"text": text}, event="rejected")
            elif ctype == "delta":
                yield _sse_event({"text": text}, event="delta")
            elif ctype == "done":
                yield _sse_event({"text": text}, event="done")
    except Exception as exc:  # noqa: BLE001
        yield _sse_event({"detail": f"답변 생성 실패: {exc!s}"}, event="error")
