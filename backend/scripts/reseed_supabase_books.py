"""Supabase public.books 전체 삭제 후, 로컬 카탈로그에서 필터링한 뒤 섹터별 N권씩 다시 upsert.

  API로 새로 받아오려면: `backend/scripts/sync_supabase_books_from_api.py` 사용.

  - 어린이·교육용 제외: backend/scripts/book_catalog_filters.py 규칙
  - KDC 섹터 0~9 각각 최대 --per-sector 권 (기본 50)

사전 준비:
  pip install -r backend/scripts/requirements-seed.txt

환경 변수 (민감값은 직접 설정):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY

실행 (저장소 루트):
  python backend/scripts/reseed_supabase_books.py
  python backend/scripts/reseed_supabase_books.py --dry-run
  python backend/scripts/reseed_supabase_books.py path/to/books.json --per-sector 50
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from book_catalog_filters import pick_per_sector, should_keep_book

REPO = _SCRIPTS.parent.parent
DEFAULT_JSON = REPO / "frontend" / "src" / "data" / "booksCatalog.json"
BATCH = 500


def _load_env() -> None:
    if not load_dotenv:
        return
    p = REPO / ".env"
    if p.is_file():
        load_dotenv(p)


def row_for_db(obj: dict) -> dict:
    return {
        "id": str(obj.get("id", "")),
        "title": (obj.get("title") or "")[:20000],
        "authors": (obj.get("authors") or "")[:20000],
        "description": (obj.get("description") or "")[:50000],
        "author_bio": (obj.get("author_bio") or "")[:20000],
        "editorial_review": (obj.get("editorial_review") or "")[:50000],
        "publisher": (obj.get("publisher") or "")[:500],
        "published_year": str(obj.get("published_year") or "")[:32],
        "kdc_class_no": (obj.get("kdc_class_no") or "")[:64],
        "kdc_class_nm": (obj.get("kdc_class_nm") or "")[:500],
        "sector": int(obj.get("sector") or 0),
        "cover_image_url": (obj.get("cover_image_url") or "")[:2000],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Supabase books 테이블 재시드 (필터 + 섹터별 상한)")
    ap.add_argument(
        "json_path",
        nargs="?",
        default=str(DEFAULT_JSON),
        help=f"카탈로그 JSON (기본: {DEFAULT_JSON})",
    )
    ap.add_argument("--per-sector", type=int, default=50, help="섹터(0~9)당 최대 권수 (기본 50)")
    ap.add_argument("--dry-run", action="store_true", help="DB 쓰기 없이 통계만 출력")
    args = ap.parse_args()

    _load_env()
    url = (os.environ.get("SUPABASE_URL") or "").strip()
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not args.dry_run and (not url or not key):
        print("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment.", file=sys.stderr)
        return 1

    json_path = Path(args.json_path).resolve()
    if not json_path.is_file():
        print(f"Missing file: {json_path}", file=sys.stderr)
        return 1

    with open(json_path, encoding="utf-8") as f:
        rows_in = json.load(f)
    if not isinstance(rows_in, list):
        print("JSON must be an array of book objects.", file=sys.stderr)
        return 1

    total_in = len(rows_in)
    kept = [r for r in rows_in if r.get("id") and should_keep_book(r)]
    dropped = total_in - len(kept)
    picked = pick_per_sector(kept, per_sector=args.per_sector)
    rows = [row_for_db(r) for r in picked]

    # 섹터별 통계
    by_sec: dict[int, int] = {i: 0 for i in range(10)}
    for r in picked:
        try:
            s = int(r.get("sector") or 0)
        except (TypeError, ValueError):
            s = 0
        if 0 <= s <= 9:
            by_sec[s] = by_sec.get(s, 0) + 1

    print(f"입력: {total_in}권 / 필터 통과: {len(kept)}권 (제외 {dropped}권) / 업서트 예정: {len(rows)}권")
    print("섹터별(0~9) 권수:", ", ".join(f"{i}:{by_sec[i]}" for i in range(10)))
    short = [i for i in range(10) if by_sec[i] < args.per_sector]
    if short:
        need = ", ".join(str(i) for i in short)
        print(
            f"[주의] 섹터 {need} 는 필터 후 후보가 {args.per_sector}권 미만입니다. "
            "더 많은 원본 데이터(예: booksCatalog.json 확장)가 필요합니다.",
            file=sys.stderr,
        )

    if args.dry_run:
        print("Dry-run - DB 변경 없음.")
        return 0

    try:
        from supabase import create_client
    except ImportError:
        print("Install: pip install -r backend/scripts/requirements-seed.txt", file=sys.stderr)
        return 1

    client = create_client(url, key)

    print("기존 books 행 삭제 중…")
    try:
        client.table("books").delete().gte("sector", 0).execute()
    except Exception as e:
        print(f"Delete error: {e}", file=sys.stderr)
        return 1

    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        try:
            client.table("books").upsert(chunk, on_conflict="id").execute()
        except Exception as e:
            print(f"Upsert error: {e}", file=sys.stderr)
            return 1
        print(f"Upserted {min(i + len(chunk), len(rows))} / {len(rows)}")

    print(f"완료. Supabase books = {len(rows)}권 (소스: {json_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
