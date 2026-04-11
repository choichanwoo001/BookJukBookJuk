"""정보나루 loanItemSrch + 상세(srchDtlList) + 알라딘으로 섹터(0~9)별 N권 수집 후 Supabase books 전체 교체.

  - 기존 Supabase `books` 행은 삭제 후 upsert (로컬 JSON은 수정하지 않음)
  - 어린이·교육용 제외: `book_catalog_filters.should_keep_book`

필요 환경 변수 (터미널에서 설정하거나 저장소 루트 `.env`):
  LIBRARY_API_KEY   — 정보나루 (필수)
  ALADIN_API_KEY    — 알라딘 TTB (필수, 설명·표지 등 품질·필터용)
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY

실행 (저장소 루트):
  pip install -r backend/scripts/requirements-seed.txt
  python backend/scripts/sync_supabase_books_from_api.py

옵션:
  --per-sector 50
  --dry-run       Supabase 쓰기 생략, 수집만 시험
  --max-pages 20  섹터당 loanItemSrch 최대 페이지(200권/페이지)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import httpx

_SCRIPTS = Path(__file__).resolve().parent
REPO = _SCRIPTS.parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(REPO / "ai") not in sys.path:
    sys.path.insert(0, str(REPO / "ai"))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from book_catalog_filters import should_keep_book  # noqa: E402
from taste_analysis.library_api import (  # noqa: E402
    BASE_URL,
    fetch_book_details_batch,
    _get_api_error_message,
)

ALADIN_BASE = "https://www.aladin.co.kr/ttb/api"
BATCH = 500
INTER_PAGE_SEC = 1.0
ALADIN_DELAY_SEC = 0.12
DETAIL_CHUNK = 40
KDC_NAMES = {
    0: "총류",
    1: "철학",
    2: "종교",
    3: "사회과학",
    4: "자연과학",
    5: "기술과학",
    6: "예술",
    7: "언어",
    8: "문학",
    9: "역사",
}


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


async def fetch_aladin_item(client: httpx.AsyncClient, api_key: str, isbn13: str) -> dict:
    if not api_key:
        return {}
    try:
        resp = await client.get(
            f"{ALADIN_BASE}/ItemLookUp.aspx",
            params={
                "ttbkey": api_key,
                "itemIdType": "ISBN13",
                "ItemId": isbn13,
                "output": "js",
                "Version": "20131101",
                "OptResult": "authorInfo,Toc,story,reviewList",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("item", [])
        return items[0] if items else {}
    except Exception:
        return {}


def merge_library_aladin(
    sector: int,
    lib: dict,
    aladin: dict,
) -> dict | None:
    isbn = str(lib.get("isbn13") or "").strip()
    if not isbn:
        return None
    title = (lib.get("title") or aladin.get("title") or "").strip()
    if not title:
        return None
    authors = (lib.get("authors") or aladin.get("author", "") or "").strip()
    pub_lib = (lib.get("publisher") or "").strip()
    pub_ala = (aladin.get("publisher") or "").strip()
    publisher = pub_lib or pub_ala

    description = (aladin.get("description") or "").strip()
    author_bio_list = aladin.get("authorInfo", [])
    if isinstance(author_bio_list, list):
        author_bio = " ".join(
            a.get("authorInfo", "") for a in author_bio_list if isinstance(a, dict)
        )
    else:
        author_bio = str(aladin.get("authorInfoAdd") or "")

    editorial_reviews = aladin.get("reviewList", []) or []
    editorial_review = " ".join(
        (r.get("reviewRank", "") or "") + " " + (r.get("reviewText", "") or "")
        for r in editorial_reviews
        if isinstance(r, dict)
    )

    pub_date = aladin.get("pubDate") or ""
    published_year = pub_date[:4] if pub_date else ""

    cover = aladin.get("cover") or aladin.get("coverUrl") or ""
    if isinstance(cover, dict):
        cover = cover.get("url", "") or ""

    return {
        "id": isbn,
        "title": title,
        "authors": authors,
        "description": description,
        "author_bio": author_bio.strip(),
        "editorial_review": editorial_review.strip(),
        "publisher": publisher,
        "published_year": published_year,
        "kdc_class_no": (lib.get("class_no") or "")[:64],
        "kdc_class_nm": (lib.get("class_nm") or "")[:500],
        "sector": sector,
        "cover_image_url": str(cover)[:2000] if cover else "",
    }


async def fetch_loan_page(
    client: httpx.AsyncClient,
    auth_key: str,
    sector: int,
    page_no: int,
) -> list[str]:
    resp = await client.get(
        f"{BASE_URL}/loanItemSrch",
        params={
            "authKey": auth_key,
            "kdc": str(sector),
            "pageSize": "200",
            "pageNo": str(page_no),
            "format": "json",
        },
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()
    err = _get_api_error_message(data)
    if err:
        raise RuntimeError(err)
    docs = data.get("response", {}).get("docs", [])
    if isinstance(docs, dict):
        docs = [docs]
    isbns: list[str] = []
    for doc in docs:
        entry = doc.get("doc", doc)
        isbn = str(entry.get("isbn13") or entry.get("isbn") or "").strip()
        if isbn:
            isbns.append(isbn)
    return isbns


async def collect_sector(
    client: httpx.AsyncClient,
    library_key: str,
    aladin_key: str,
    sector: int,
    target: int,
    max_pages: int,
    seen_global: set[str],
    sem: asyncio.Semaphore,
) -> list[dict]:
    """섹터당 target권(필터 통과) 수집."""
    out: list[dict] = []
    page = 1
    while len(out) < target and page <= max_pages:
        try:
            isbns = await fetch_loan_page(client, library_key, sector, page)
        except Exception as e:
            print(f"  [섹터 {sector}] loanItemSrch 페이지 {page} 실패: {e}", file=sys.stderr)
            break
        if not isbns:
            break

        fresh = [i for i in isbns if i not in seen_global]
        for start in range(0, len(fresh), DETAIL_CHUNK):
            chunk = fresh[start : start + DETAIL_CHUNK]
            if not chunk:
                continue
            details = await fetch_book_details_batch(client, library_key, chunk)
            by_isbn = {str(d.get("isbn13", "")).strip(): d for d in details if d.get("isbn13")}

            async def one(isbn: str) -> dict | None:
                async with sem:
                    await asyncio.sleep(ALADIN_DELAY_SEC)
                    lib = by_isbn.get(isbn)
                    if not lib:
                        return None
                    aladin = await fetch_aladin_item(client, aladin_key, isbn)
                    row = merge_library_aladin(sector, lib, aladin)
                    if not row:
                        return None
                    if not should_keep_book(row):
                        return None
                    return row

            tasks = [one(isbn) for isbn in chunk if isbn in by_isbn and isbn not in seen_global]
            results = await asyncio.gather(*tasks)
            for r in results:
                if r is None:
                    continue
                iid = str(r["id"])
                if iid in seen_global:
                    continue
                seen_global.add(iid)
                out.append(r)
                tit = r["title"] or ""
                tshow = (tit[:42] + "…") if len(tit) > 42 else tit
                print(f"  [{KDC_NAMES.get(sector, sector)}] {len(out)}/{target} ISBN {iid} — {tshow}")
                if len(out) >= target:
                    return out[:target]

        page += 1
        await asyncio.sleep(INTER_PAGE_SEC)

    return out


async def run_async(args: argparse.Namespace) -> list[dict]:
    library_key = (os.environ.get("LIBRARY_API_KEY") or "").strip()
    aladin_key = (os.environ.get("ALADIN_API_KEY") or "").strip()
    if not library_key:
        raise SystemExit("LIBRARY_API_KEY 가 필요합니다.")
    if not aladin_key:
        raise SystemExit("ALADIN_API_KEY 가 필요합니다 (설명·필터용).")

    all_rows: list[dict] = []
    seen: set[str] = set()
    sem = asyncio.Semaphore(6)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for sector in range(10):
            print(f"\n=== 섹터 {sector} ({KDC_NAMES[sector]}) — 목표 {args.per_sector}권 ===")
            rows = await collect_sector(
                client,
                library_key,
                aladin_key,
                sector,
                args.per_sector,
                args.max_pages,
                seen,
                sem,
            )
            all_rows.extend(rows)
            if len(rows) < args.per_sector:
                print(
                    f"  [경고] 섹터 {sector}: 필터 후 {len(rows)}권만 확보 "
                    f"(목표 {args.per_sector}). 후보를 늘리려면 --max-pages 를 키우세요.",
                    file=sys.stderr,
                )
    return all_rows


def main() -> int:
    _load_env()

    ap = argparse.ArgumentParser(description="정보나루+알라딘으로 Supabase books 재구축")
    ap.add_argument("--per-sector", type=int, default=50, help="KDC 섹터(0~9)당 권수 (기본 50)")
    ap.add_argument("--max-pages", type=int, default=25, help="섹터당 loanItemSrch 최대 페이지")
    ap.add_argument("--dry-run", action="store_true", help="Supabase 삭제/upsert 생략")
    args = ap.parse_args()

    url = (os.environ.get("SUPABASE_URL") or "").strip()
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not args.dry_run and (not url or not key):
        print("SUPABASE_URL 과 SUPABASE_SERVICE_ROLE_KEY 가 필요합니다 (--dry-run 이면 생략 가능).", file=sys.stderr)
        return 1

    rows = asyncio.run(run_async(args))
    db_rows = [row_for_db(r) for r in rows]
    print(f"\n총 {len(db_rows)}권 수집 (섹터당 최대 {args.per_sector} 목표).")

    if args.dry_run:
        print("Dry-run: Supabase 반영 없음.")
        return 0

    try:
        from supabase import create_client
    except ImportError:
        print("pip install -r backend/scripts/requirements-seed.txt", file=sys.stderr)
        return 1

    client = create_client(url, key)
    print("Supabase books 기존 데이터 삭제 중…")
    try:
        client.table("books").delete().gte("sector", 0).execute()
    except Exception as e:
        print(f"Delete error: {e}", file=sys.stderr)
        return 1

    for i in range(0, len(db_rows), BATCH):
        chunk = db_rows[i : i + BATCH]
        try:
            client.table("books").upsert(chunk, on_conflict="id").execute()
        except Exception as e:
            print(f"Upsert error: {e}", file=sys.stderr)
            return 1
        print(f"Upserted {min(i + len(chunk), len(db_rows))} / {len(db_rows)}")

    print("완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
