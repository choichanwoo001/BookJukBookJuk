"""책 표지용 알라딘 프록시 — GET /api/book-cover → 알라딘 표지 URL 또는 Open Library로 리다이렉트."""
from __future__ import annotations

import re
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse

ROOT = Path(__file__).resolve().parent.parent
_env = ROOT / ".env"
if _env.is_file():
    load_dotenv(_env)

ALADIN_LOOKUP = "https://www.aladin.co.kr/ttb/api/ItemLookUp.aspx"

app = FastAPI(title="BookJukBookJuk API", version="0.1.0")


def _aladin_key() -> str:
    import os

    return (os.getenv("ALADIN_API_KEY") or os.getenv("ALADIN_TTB_KEY") or "").strip()


def _normalize_isbn(isbn: str) -> str:
    return re.sub(r"[^0-9X]", "", isbn, flags=re.I)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/book-cover")
def book_cover(isbn13: str = Query(..., alias="isbn13", description="ISBN-13")) -> RedirectResponse:
    isbn = _normalize_isbn(isbn13)
    open_lib = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"

    if len(isbn) != 13:
        # 백엔드 단독 호출 시 상대 경로는 호스트가 달라 깨지므로 Open Library 고정 폴백
        return RedirectResponse(
            url="https://covers.openlibrary.org/b/isbn/9788936434120-M.jpg",
            status_code=302,
        )

    key = _aladin_key()
    if not key:
        return RedirectResponse(url=open_lib, status_code=302)

    try:
        params = {
            "ttbkey": key,
            "itemIdType": "ISBN13",
            "ItemId": isbn,
            "output": "js",
            "Version": "20131101",
        }
        with httpx.Client(timeout=10.0) as client:
            r = client.get(ALADIN_LOOKUP, params=params)
        r.raise_for_status()
        data = r.json()
        raw = data.get("item")
        items = raw if isinstance(raw, list) else ([raw] if raw else [])
        item = items[0] if items else {}
        cover = item.get("cover")
        if isinstance(cover, str) and re.match(r"^https?://", cover, re.I):
            return RedirectResponse(url=cover, status_code=302)
    except Exception:
        pass

    return RedirectResponse(url=open_lib, status_code=302)
