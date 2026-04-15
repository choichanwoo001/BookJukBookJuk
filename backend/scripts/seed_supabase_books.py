"""booksCatalog.json(또는 export 스크립트 결과)을 Supabase public.books 에 upsert 합니다.

사전 준비:
  pip install -r requirements.txt

환경 변수 (터미널에 직접 설정하거나, 다른 스크립트와 같이 저장소 루트 `.env`에 두는 방식):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY  (anon 키가 아님 — 서버/로컬 시드 전용)

실행 (저장소 루트에서):
  python backend/scripts/seed_supabase_books.py
  python backend/scripts/seed_supabase_books.py path/to/custom.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from book_catalog_db_limits import (
    MAX_CHARS_ALADIN_COVER_URL,
    MAX_CHARS_ALADIN_LONG_TEXT,
    MAX_CHARS_ALADIN_MEDIUM_TEXT,
    MAX_CHARS_KDC_CLASS_NM,
    MAX_CHARS_KDC_CLASS_NO,
    MAX_CHARS_PUBLISHED_YEAR,
    MAX_CHARS_PUBLISHER,
    clip,
)

REPO = Path(__file__).resolve().parent.parent.parent
DEFAULT_JSON = REPO / "frontend" / "src" / "data" / "booksCatalog.json"
BATCH = 500


def row_for_db(obj: dict) -> dict:
    """로컬 JSON → Supabase upsert. 문자열 상한은 `book_catalog_db_limits` (sync·reseed 와 동일)."""
    return {
        "id": str(obj.get("id", "")),
        "title": clip(obj.get("title"), MAX_CHARS_ALADIN_MEDIUM_TEXT),
        "authors": clip(obj.get("authors"), MAX_CHARS_ALADIN_MEDIUM_TEXT),
        "description": clip(obj.get("description"), MAX_CHARS_ALADIN_LONG_TEXT),
        "author_bio": clip(obj.get("author_bio"), MAX_CHARS_ALADIN_MEDIUM_TEXT),
        "editorial_review": clip(obj.get("editorial_review"), MAX_CHARS_ALADIN_LONG_TEXT),
        "publisher": clip(obj.get("publisher"), MAX_CHARS_PUBLISHER),
        "published_year": clip(str(obj.get("published_year") or ""), MAX_CHARS_PUBLISHED_YEAR),
        "kdc_class_no": clip(obj.get("kdc_class_no"), MAX_CHARS_KDC_CLASS_NO),
        "kdc_class_nm": clip(obj.get("kdc_class_nm"), MAX_CHARS_KDC_CLASS_NM),
        "sector": int(obj.get("sector") or 0),
        "cover_image_url": clip(obj.get("cover_image_url"), MAX_CHARS_ALADIN_COVER_URL),
    }


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(REPO / ".env")
    except ImportError:
        pass

    try:
        from supabase import create_client
    except ImportError:
        print("Install: pip install supabase", file=sys.stderr)
        return 1

    url = (os.environ.get("SUPABASE_URL") or "").strip()
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not url or not key:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment.", file=sys.stderr)
        return 1

    json_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_JSON
    if not json_path.is_file():
        print(f"Missing file: {json_path}", file=sys.stderr)
        return 1

    with open(json_path, encoding="utf-8") as f:
        rows_in = json.load(f)
    if not isinstance(rows_in, list):
        print("JSON must be an array of book objects.", file=sys.stderr)
        return 1

    rows = [row_for_db(r) for r in rows_in if r.get("id")]
    client = create_client(url, key)

    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        try:
            client.table("books").upsert(chunk, on_conflict="id").execute()
        except Exception as e:
            print(f"Upsert error: {e}", file=sys.stderr)
            return 1
        print(f"Upserted {min(i + len(chunk), len(rows))} / {len(rows)}")

    print(f"Done. Total {len(rows)} books from {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
