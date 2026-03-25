"""1000권 수집 오케스트레이터.

KDC 10개 섹터(0-9) × 100권씩 수집하며:
  - 저자 Wikipedia 페이지 필수 (없으면 스킵)
  - 전체 400권은 한국 저자 + 2020년 이후 출판
  - 섹터별 KR 쿼터 자동 조정
  - DB에 이미 있는 ISBN은 스킵 (resume 지원)
"""
from __future__ import annotations

import asyncio
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taste_analysis.library_api import fetch_book_detail
from book_chat.data_collector import collect_book_context

from .db import (
    DB_PATH,
    BookRow,
    count_korean_recent_by_sector,
    count_sector,
    insert_keywords,
    insert_raw_docs,
    isbn_exists,
    upsert_book,
)
from .wiki_checker import check_author_wiki
from .korean_checker import is_korean_author, is_recent

# ── 상수 ──────────────────────────────────────────────────────────────────
LIBRARY_BASE = "http://data4library.kr/api"
CANDIDATES_PER_SECTOR = 600   # 섹터당 후보 ISBN 최대 수
TARGET_PER_SECTOR = 100        # 섹터당 저장 목표
TOTAL_KR_TARGET = 400          # 전체 한국 최근 도서 목표

INTER_PAGE_DELAY = 1.0         # loanItemSrch 페이지 간 대기 (초)
WIKI_CHECK_DELAY = 0.5         # Wikipedia 체크 후 대기 (초)
COLLECT_DELAY = 2.0            # collect_book_context 호출 후 대기 (초)

# 한국 최근 책이 많을 가능성이 높은 섹터부터 처리
SECTOR_ORDER = [8, 3, 9, 1, 5, 4, 6, 2, 7, 0]

KDC_NAMES = {
    0: "총류", 1: "철학", 2: "종교", 3: "사회과학", 4: "자연과학",
    5: "기술과학", 6: "예술", 7: "언어", 8: "문학", 9: "역사",
}


def _extract_api_error(data: dict) -> str | None:
    """정보나루 API 응답에 에러 메시지가 있으면 반환."""
    res = data.get("response", {}) or {}
    if isinstance(res, dict) and res.get("error"):
        return str(res["error"])
    return None


async def fetch_candidates_for_sector(
    sector: int,
    library_api_key: str,
    max_candidates: int = CANDIDATES_PER_SECTOR,
) -> list[str]:
    """정보나루 loanItemSrch로 섹터별 후보 ISBN 목록 수집 (페이지네이션 지원)."""
    isbns: list[str] = []
    seen: set[str] = set()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for page_no in range(1, 6):  # 최대 5페이지 × 200 = 1000 후보
            if len(isbns) >= max_candidates:
                break
            try:
                resp = await client.get(
                    f"{LIBRARY_BASE}/loanItemSrch",
                    params={
                        "authKey": library_api_key,
                        "kdc": str(sector),
                        "pageSize": "200",
                        "pageNo": str(page_no),
                        "format": "json",
                    },
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()

                err = _extract_api_error(data)
                if err:
                    print(f"  [Sector {sector}] API 오류 (page {page_no}): {err}")
                    break

                docs = data.get("response", {}).get("docs", [])
                if isinstance(docs, dict):
                    docs = [docs]
                if not docs:
                    break

                new_count = 0
                for doc in docs:
                    entry = doc.get("doc", doc)
                    isbn = str(entry.get("isbn13") or entry.get("isbn") or "").strip()
                    if isbn and isbn not in seen:
                        seen.add(isbn)
                        isbns.append(isbn)
                        new_count += 1

                print(
                    f"  [Sector {sector}] Page {page_no}: {new_count}개 후보 "
                    f"(누적 {len(isbns)}개)"
                )
                if new_count == 0 or len(docs) < 200:
                    break  # 마지막 페이지

                await asyncio.sleep(INTER_PAGE_DELAY)

            except Exception as e:
                print(f"  [Sector {sector}] 후보 조회 실패 (page {page_no}): {e}")
                break

    return isbns[:max_candidates]


async def _process_isbn(
    isbn13: str,
    sector: int,
    library_api_key: str,
    aladin_api_key: str,
    detail_client: httpx.AsyncClient,
    wiki_client: httpx.AsyncClient,
    db_path: str,
) -> tuple[bool, bool, bool]:
    """한 ISBN을 처리해 DB에 저장.

    Returns:
        (inserted, is_korean, is_rec)
        inserted=False이면 스킵됨.
    """
    # 1. 기본 정보 조회 (정보나루)
    try:
        detail = await fetch_book_detail(detail_client, library_api_key, isbn13)
    except Exception as e:
        print(f"    [SKIP] {isbn13} 정보나루 조회 실패: {e}")
        return False, False, False

    authors_str = detail.get("authors", "")
    title_str = detail.get("title", "")
    if not authors_str and not title_str:
        return False, False, False

    # 2. Wikipedia 저자 체크 (경량 pre-filter)
    has_wiki, wiki_lang, author_summary = await check_author_wiki(authors_str, wiki_client)
    await asyncio.sleep(WIKI_CHECK_DELAY)

    if not has_wiki:
        return False, False, False

    # 3. 전체 데이터 수집 (Aladin + 정보나루 + Wikipedia)
    try:
        ctx = await collect_book_context(
            isbn13=isbn13,
            library_api_key=library_api_key,
            aladin_api_key=aladin_api_key,
        )
        await asyncio.sleep(COLLECT_DELAY)
    except Exception as e:
        print(f"    [SKIP] {isbn13} collect_book_context 실패: {e}")
        return False, False, False

    if not ctx.title:
        return False, False, False

    # 4. 분류
    final_authors = ctx.authors or authors_str
    is_korean = is_korean_author(final_authors)
    is_rec = is_recent(ctx.published_year)

    # 5. DB 저장
    row = BookRow(
        isbn13=ctx.isbn13 or isbn13,
        isbn10=None,
        title=ctx.title,
        authors=final_authors,
        publisher=ctx.publisher,
        published_year=ctx.published_year,
        description=ctx.description,
        author_bio=ctx.author_bio,
        editorial_review=ctx.editorial_review,
        kdc_class_no=detail.get("class_no", ""),
        kdc_class_nm=ctx.kdc_class or detail.get("class_nm", ""),
        sector=sector,
        wiki_book_summary=ctx.wiki_book_summary,
        wiki_author_summary=ctx.wiki_author_summary or author_summary,
        wiki_lang=wiki_lang,
        cover_image_url=None,
        is_korean_author=is_korean,
        is_recent=is_rec,
    )
    try:
        upsert_book(row, db_path)
        insert_keywords(isbn13, ctx.keywords, db_path)
        insert_raw_docs(isbn13, ctx.raw_docs, db_path)
    except Exception as e:
        print(f"    [WARN] {isbn13} DB 저장 실패: {e}")
        return False, False, False

    return True, is_korean, is_rec


async def run_sector(
    sector: int,
    library_api_key: str,
    aladin_api_key: str,
    kr_target: int,
    db_path: str = DB_PATH,
) -> tuple[int, int]:
    """한 섹터의 책을 TARGET_PER_SECTOR권 수집.

    Returns:
        (total_saved, korean_recent_saved)
    """
    initial_saved = count_sector(sector, db_path)
    if initial_saved >= TARGET_PER_SECTOR:
        kr_count = count_korean_recent_by_sector(db_path).get(sector, 0)
        print(f"[Sector {sector} {KDC_NAMES[sector]}] 이미 완료 ({initial_saved}권). 스킵.")
        return initial_saved, kr_count

    print(f"\n{'='*60}")
    print(f"[Sector {sector} {KDC_NAMES[sector]}] 시작")
    print(f"  기존: {initial_saved}권 / 목표: {TARGET_PER_SECTOR}권 / KR목표: {kr_target}권")
    print(f"{'='*60}")

    candidates = await fetch_candidates_for_sector(sector, library_api_key)
    print(f"[Sector {sector}] 총 {len(candidates)}개 후보 확보\n")

    saved = initial_saved
    kr_saved = count_korean_recent_by_sector(db_path).get(sector, 0)

    async with httpx.AsyncClient(timeout=15.0) as wiki_client:
        async with httpx.AsyncClient(timeout=15.0) as detail_client:
            for isbn13 in candidates:
                if saved >= TARGET_PER_SECTOR:
                    break

                if isbn_exists(isbn13, db_path):
                    continue

                try:
                    inserted, is_korean, is_rec = await _process_isbn(
                        isbn13=isbn13,
                        sector=sector,
                        library_api_key=library_api_key,
                        aladin_api_key=aladin_api_key,
                        detail_client=detail_client,
                        wiki_client=wiki_client,
                        db_path=db_path,
                    )
                except KeyboardInterrupt:
                    print("\n[중단] 사용자에 의해 중단되었습니다.")
                    raise
                except Exception as e:
                    print(f"  [WARN] {isbn13} 처리 중 예외: {e}")
                    continue

                if inserted:
                    saved += 1
                    if is_korean and is_rec:
                        kr_saved += 1
                    kr_label = " [KR최근]" if (is_korean and is_rec) else ""
                    print(
                        f"  [{saved}/{TARGET_PER_SECTOR}] 저장{kr_label} | "
                        f"KR: {kr_saved}/{kr_target} | ISBN: {isbn13}"
                    )

    print(
        f"\n[Sector {sector} {KDC_NAMES[sector]}] 완료: "
        f"{saved}권 / KR최근: {kr_saved}/{kr_target}\n"
    )
    return saved, kr_saved


async def run_all_sectors(
    library_api_key: str,
    aladin_api_key: str,
    db_path: str = DB_PATH,
) -> None:
    """10개 섹터 전체 실행 (KR 쿼터 자동 조정)."""
    remaining_kr = TOTAL_KR_TARGET
    remaining_sectors = len(SECTOR_ORDER)
    total_saved = 0
    total_kr = 0

    for sector in SECTOR_ORDER:
        kr_target = remaining_kr // remaining_sectors if remaining_sectors > 0 else 0

        saved, kr_saved = await run_sector(
            sector=sector,
            library_api_key=library_api_key,
            aladin_api_key=aladin_api_key,
            kr_target=kr_target,
            db_path=db_path,
        )

        total_saved += saved
        total_kr += kr_saved
        remaining_kr = max(0, remaining_kr - kr_saved)
        remaining_sectors -= 1

        if remaining_kr > 0 and remaining_sectors > 0:
            new_target = remaining_kr // remaining_sectors
            print(
                f"  → 남은 KR 목표: {remaining_kr}권 / "
                f"남은 섹터: {remaining_sectors}개 / "
                f"다음 섹터 KR 목표: {new_target}권"
            )

    print(f"\n{'='*60}")
    print("전체 완료!")
    print(f"  총 저장: {total_saved}권")
    print(f"  한국 최근: {total_kr}권 (목표: {TOTAL_KR_TARGET}권)")
    print(f"  DB 위치: {db_path}")
    print(f"{'='*60}")
