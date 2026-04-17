"""FastAPI: 표지 프록시, 하이브리드 추천, 책 조회 API."""
from __future__ import annotations

from datetime import datetime, timezone
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse

ROOT = Path(__file__).resolve().parent.parent
_AI_DIR = ROOT / "ai"
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))
_env = ROOT / ".env"
if _env.is_file():
    load_dotenv(_env)

ALADIN_LOOKUP = "https://www.aladin.co.kr/ttb/api/ItemLookUp.aspx"

app = FastAPI(title="BookJukBookJuk API", version="0.1.0")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _default_book_image(book_id: str, cover_image_url: str | None = None) -> str:
    cover = (cover_image_url or "").strip()
    if cover:
        return cover
    return f"/api/book-cover?isbn13={book_id}"


def _map_book_row(row: dict[str, Any]) -> dict[str, Any]:
    book_id = str(row.get("id") or "").strip()
    published_year = str(row.get("published_year") or "").strip()
    return {
        "id": book_id,
        "title": str(row.get("title") or "").strip(),
        "authors": str(row.get("authors") or "").strip(),
        "description": str(row.get("description") or "").strip(),
        "authorBio": str(row.get("author_bio") or "").strip(),
        "publisher": str(row.get("publisher") or "").strip(),
        "publishedYear": published_year,
        "productionYear": _safe_int(re.search(r"\d{4}", published_year).group(0), 0)
        if re.search(r"\d{4}", published_year)
        else 0,
        "kdcClassNo": str(row.get("kdc_class_no") or "").strip(),
        "kdcClassNm": str(row.get("kdc_class_nm") or "").strip(),
        "category": str(row.get("kdc_class_nm") or "").split(">")[-1].strip()
        if str(row.get("kdc_class_nm") or "").strip()
        else "",
        "coverImageUrl": str(row.get("cover_image_url") or "").strip(),
        "image": _default_book_image(book_id, row.get("cover_image_url")),
    }


def _supabase_client() -> Any | None:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def _must_supabase() -> Any:
    sb = _supabase_client()
    if not sb:
        raise HTTPException(
            status_code=503,
            detail="SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY(또는 ANON_KEY) 설정이 필요합니다.",
        )
    return sb


def _fetch_books_by_ids(sb: Any, book_ids: list[str]) -> dict[str, dict[str, Any]]:
    ids = [str(x).strip() for x in book_ids if str(x).strip()]
    if not ids:
        return {}
    res = (
        sb.table("books")
        .select(
            "id, title, authors, description, author_bio, publisher, published_year, kdc_class_no, kdc_class_nm, cover_image_url"
        )
        .in_("id", ids)
        .execute()
    )
    data = res.data or []
    return {str(row.get("id")): _map_book_row(row) for row in data}


def _ratings_map_for_books(sb: Any, book_ids: list[str]) -> dict[str, float]:
    ids = [str(x).strip() for x in book_ids if str(x).strip()]
    if not ids:
        return {}
    res = sb.table("ratings").select("books_id, score").in_("books_id", ids).execute()
    rows = res.data or []
    bucket: dict[str, list[float]] = {}
    for row in rows:
        bid = str(row.get("books_id") or "").strip()
        if not bid:
            continue
        bucket.setdefault(bid, []).append(_safe_float(row.get("score"), 0.0))
    out: dict[str, float] = {}
    for bid, scores in bucket.items():
        if scores:
            out[bid] = round(sum(scores) / len(scores), 1)
    return out


def _decorate_books_with_rating(sb: Any, books: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = [str(b.get("id") or "") for b in books]
    ratings = _ratings_map_for_books(sb, ids)
    out = []
    for b in books:
        bid = str(b.get("id") or "")
        out.append({**b, "rating": ratings.get(bid, 0.0)})
    return out


def _aladin_key() -> str:
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


@app.get("/api/recommendations")
async def recommendations(
    limit: int = Query(4, ge=1, le=30, description="추천 권수"),
    user_id: str = Query(
        "dev_user_1",
        description="Supabase users.users_id 와 동일한 사용자 식별자",
    ),
    with_explanation: bool = Query(
        False,
        description="True면 LLM 설명 생성(느림). 홈 행에는 false 권장.",
    ),
) -> dict:
    """하이브리드 추천 파이프라인 결과. Supabase에 KG·벡터·사용자 이력이 있어야 의미 있는 결과가 나옵니다."""
    try:
        from hybrid_recommender import HybridRecommenderPipeline
        from hybrid_recommender.supabase_user_profile import load_user_profile_from_supabase
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"hybrid_recommender 로드 실패: {e}") from e

    try:
        pipeline = HybridRecommenderPipeline.from_env(user_id=user_id.strip() or "dev_user_1")
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    sb = pipeline.supabase_client
    if sb and user_id.strip():
        pipeline.user_profile = load_user_profile_from_supabase(sb, user_id.strip())

    if pipeline.kg.node_count() == 0 and len(pipeline.vector_store) == 0:
        raise HTTPException(
            status_code=503,
            detail="추천 엔진에 로드된 KG/벡터가 없습니다. Supabase 시드 및 HYBRID_PERSIST_* 설정을 확인하세요.",
        )

    try:
        results = await pipeline.recommend(
            top_k=limit,
            with_explanation=with_explanation,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"recommend 실패: {e!s}") from e

    items = []
    for r in results:
        items.append(
            {
                "id": r.isbn13,
                "isbn13": r.isbn13,
                "title": r.title,
                "authors": r.authors or "",
                "final_score": r.final_score,
                "graph_score": r.graph_score,
                "vector_score": r.vector_score,
                "alpha_used": r.alpha_used,
                "kdc_class": r.kdc_class or "",
                "publisher": r.publisher or "",
                "published_year": r.published_year or "",
                "explanation": getattr(r, "explanation", None) or "",
            }
        )
    return {"items": items}


@app.get("/api/books/search")
def search_books(
    q: str = Query("", description="검색어(제목/저자)"),
    limit: int = Query(20, ge=1, le=100, description="최대 결과 수"),
) -> dict[str, Any]:
    sb = _must_supabase()
    query = q.strip()
    if not query:
        return {"items": []}
    like = f"%{query}%"
    res = (
        sb.table("books")
        .select(
            "id, title, authors, description, author_bio, publisher, published_year, kdc_class_no, kdc_class_nm, cover_image_url"
        )
        .or_(f"title.ilike.{like},authors.ilike.{like}")
        .limit(limit)
        .execute()
    )
    books = [_map_book_row(row) for row in (res.data or [])]
    return {"items": _decorate_books_with_rating(sb, books)}


@app.get("/api/books/{book_id}")
def get_book_detail(book_id: str) -> dict[str, Any]:
    sb = _must_supabase()
    res = (
        sb.table("books")
        .select(
            "id, title, authors, description, author_bio, publisher, published_year, kdc_class_no, kdc_class_nm, cover_image_url"
        )
        .eq("id", book_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    base = _map_book_row(rows[0])
    rating_map = _ratings_map_for_books(sb, [book_id])
    return {
        **base,
        "rating": rating_map.get(book_id, 0.0),
        "pages": 0,
        "ageRating": "",
        "storeLocation": {"lat": 37.5665, "lng": 126.978},
    }


@app.get("/api/books/{book_id}/comments")
def get_book_comments(
    book_id: str,
    limit: int = Query(20, ge=1, le=100, description="최대 코멘트 수"),
) -> dict[str, Any]:
    sb = _must_supabase()
    reviews_res = (
        sb.table("reviews")
        .select("reviews_id, users_id, content, created_at")
        .eq("books_id", book_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    reviews = reviews_res.data or []
    if not reviews:
        return {"items": []}

    review_ids = [str(r.get("reviews_id") or "").strip() for r in reviews if str(r.get("reviews_id") or "").strip()]
    user_ids = [str(r.get("users_id") or "").strip() for r in reviews if str(r.get("users_id") or "").strip()]

    rating_map: dict[str, float] = {}
    if user_ids:
        rres = sb.table("ratings").select("users_id, score").eq("books_id", book_id).in_("users_id", user_ids).execute()
        for row in (rres.data or []):
            rating_map[str(row.get("users_id") or "")] = _safe_float(row.get("score"), 0.0)

    user_map: dict[str, str] = {}
    if user_ids:
        ures = sb.table("users").select("users_id, nickname").in_("users_id", user_ids).execute()
        for row in (ures.data or []):
            user_map[str(row.get("users_id") or "")] = str(row.get("nickname") or "").strip()

    reply_count_map: dict[str, int] = {}
    like_count_map: dict[str, int] = {}
    for rid in review_ids:
        cres = sb.table("comments").select("comments_id", count="exact").eq("reviews_id", rid).execute()
        lres = sb.table("review_likes").select("users_id", count="exact").eq("reviews_id", rid).execute()
        reply_count_map[rid] = int(getattr(cres, "count", 0) or 0)
        like_count_map[rid] = int(getattr(lres, "count", 0) or 0)

    items = []
    for r in reviews:
        rid = str(r.get("reviews_id") or "")
        uid = str(r.get("users_id") or "")
        items.append(
            {
                "id": rid,
                "reviewId": rid,
                "userId": uid,
                "userName": user_map.get(uid) or uid or "독자",
                "text": str(r.get("content") or "").strip(),
                "rating": rating_map.get(uid, 0.0),
                "likeCount": like_count_map.get(rid, 0),
                "replyCount": reply_count_map.get(rid, 0),
                "createdAt": str(r.get("created_at") or _now_iso()),
            }
        )
    return {"items": items}


@app.get("/api/books/{book_id}/comments/{comment_id}")
def get_book_comment_detail(book_id: str, comment_id: str) -> dict[str, Any]:
    sb = _must_supabase()
    comment_res = (
        sb.table("reviews")
        .select("reviews_id, users_id, content, created_at")
        .eq("books_id", book_id)
        .eq("reviews_id", comment_id)
        .limit(1)
        .execute()
    )
    rows = comment_res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="코멘트를 찾을 수 없습니다.")
    review = rows[0]
    comments = get_book_comments(book_id, limit=1000).get("items", [])
    target = next((c for c in comments if c.get("id") == comment_id), None)
    if not target:
        target = {
            "id": comment_id,
            "reviewId": comment_id,
            "userId": str(review.get("users_id") or ""),
            "userName": str(review.get("users_id") or "독자"),
            "text": str(review.get("content") or "").strip(),
            "rating": 0.0,
            "likeCount": 0,
            "replyCount": 0,
            "createdAt": str(review.get("created_at") or _now_iso()),
        }
    return {"item": target}


@app.get("/api/sections/{section_id}/books")
async def get_section_books(
    section_id: str,
    user_id: str = Query("dev_user_1", description="사용자 ID"),
    limit: int = Query(20, ge=1, le=100, description="최대 권수"),
) -> dict[str, Any]:
    sb = _must_supabase()
    sid = section_id.strip()
    if sid == "recommend":
        data = await recommendations(limit=limit, user_id=user_id, with_explanation=False)
        items = data.get("items", [])
        return {
            "id": sid,
            "title": "영진님의 취향 저격",
            "books": [
                {
                    "id": str(it.get("id") or ""),
                    "title": str(it.get("title") or ""),
                    "authors": str(it.get("authors") or ""),
                    "image": _default_book_image(str(it.get("id") or ""), ""),
                    "rating": round(_safe_float(it.get("final_score"), 0.0), 2),
                }
                for it in items
            ],
        }
    if sid == "rating":
        rres = (
            sb.table("ratings")
            .select("books_id, score")
            .order("score", desc=True)
            .limit(max(limit * 3, 20))
            .execute()
        )
        rows = rres.data or []
        score_bucket: dict[str, list[float]] = {}
        for row in rows:
            bid = str(row.get("books_id") or "").strip()
            if not bid:
                continue
            score_bucket.setdefault(bid, []).append(_safe_float(row.get("score"), 0.0))
        avg_rows = sorted(
            [{"id": bid, "avg": (sum(vals) / len(vals))} for bid, vals in score_bucket.items() if vals],
            key=lambda x: x["avg"],
            reverse=True,
        )[:limit]
        books_map = _fetch_books_by_ids(sb, [x["id"] for x in avg_rows])
        books = []
        for x in avg_rows:
            b = books_map.get(x["id"])
            if not b:
                continue
            books.append({**b, "rating": round(float(x["avg"]), 1)})
        return {"id": sid, "title": "평균 별점이 높은 작품", "books": books}
    if sid == "wishlist":
        states_res = (
            sb.table("book_user_states")
            .select("books_id, shelf_state")
            .eq("users_id", user_id)
            .in_("shelf_state", ["LIST", "READING"])
            .limit(limit)
            .execute()
        )
        ids = [str(r.get("books_id") or "").strip() for r in (states_res.data or []) if str(r.get("books_id") or "").strip()]
        books = _decorate_books_with_rating(sb, list(_fetch_books_by_ids(sb, ids).values()))
        return {"id": sid, "title": "찜한 목록/이어읽기", "books": books[:limit]}
    # default: HOT
    hot_res = (
        sb.table("ratings")
        .select("books_id, score")
        .order("registered_at", desc=True)
        .limit(max(limit * 3, 20))
        .execute()
    )
    hot_ids: list[str] = []
    for row in hot_res.data or []:
        bid = str(row.get("books_id") or "").strip()
        if bid and bid not in hot_ids:
            hot_ids.append(bid)
        if len(hot_ids) >= limit:
            break
    books = _decorate_books_with_rating(sb, list(_fetch_books_by_ids(sb, hot_ids).values()))
    return {"id": sid or "hot", "title": "HOT 랭킹", "books": books[:limit]}


@app.get("/api/home-sections")
async def home_sections(
    user_id: str = Query("dev_user_1", description="사용자 ID"),
    limit: int = Query(4, ge=1, le=30, description="섹션별 권수"),
) -> dict[str, Any]:
    section_order = ["wishlist", "hot", "rating", "recommend"]
    sections = []
    for sid in section_order:
        sections.append(await get_section_books(section_id=sid, user_id=user_id, limit=limit))
    return {"items": sections}


@app.get("/api/users/{user_id}/collections")
def user_collections(user_id: str) -> dict[str, Any]:
    sb = _must_supabase()
    q = (
        sb.table("collections")
        .select("collections_id, users_id, title, description, is_public, created_at")
        .eq("users_id", user_id)
        .order("created_at", desc=True)
    )
    res = q.limit(20).execute()
    collections = res.data or []
    ids = [str(c.get("collections_id") or "").strip() for c in collections if str(c.get("collections_id") or "").strip()]
    books_by_collection: dict[str, list[dict[str, Any]]] = {cid: [] for cid in ids}
    if ids:
        cb = (
            sb.table("collection_books")
            .select("books_id, collections_id, order_index")
            .in_("collections_id", ids)
            .order("order_index", desc=False)
            .execute()
        )
        rows = cb.data or []
        all_book_ids = [str(r.get("books_id") or "").strip() for r in rows if str(r.get("books_id") or "").strip()]
        books_map = _fetch_books_by_ids(sb, all_book_ids)
        books_map = {k: v for k, v in books_map.items()}
        ratings = _ratings_map_for_books(sb, list(books_map.keys()))
        for row in rows:
            cid = str(row.get("collections_id") or "").strip()
            bid = str(row.get("books_id") or "").strip()
            b = books_map.get(bid)
            if not cid or not b:
                continue
            books_by_collection.setdefault(cid, []).append({**b, "rating": ratings.get(bid, 0.0)})
    items = []
    for c in collections:
        cid = str(c.get("collections_id") or "").strip()
        items.append(
            {
                "id": cid,
                "userId": str(c.get("users_id") or ""),
                "title": str(c.get("title") or "").strip(),
                "description": str(c.get("description") or "").strip(),
                "isPublic": bool(c.get("is_public")),
                "createdAt": str(c.get("created_at") or _now_iso()),
                "books": books_by_collection.get(cid, []),
            }
        )
    return {"items": items}


@app.get("/api/collections/{collection_id}")
def collection_detail(collection_id: str) -> dict[str, Any]:
    sb = _must_supabase()
    cres = (
        sb.table("collections")
        .select("collections_id, users_id, title, description, is_public, created_at")
        .eq("collections_id", collection_id)
        .limit(1)
        .execute()
    )
    rows = cres.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="컬렉션을 찾을 수 없습니다.")
    c = rows[0]
    books_res = (
        sb.table("collection_books")
        .select("books_id, collections_id, order_index, added_at")
        .eq("collections_id", collection_id)
        .order("order_index", desc=False)
        .execute()
    )
    cbooks = books_res.data or []
    book_ids = [str(r.get("books_id") or "").strip() for r in cbooks if str(r.get("books_id") or "").strip()]
    books_map = _fetch_books_by_ids(sb, book_ids)
    ratings = _ratings_map_for_books(sb, book_ids)
    books = []
    for row in cbooks:
        bid = str(row.get("books_id") or "").strip()
        b = books_map.get(bid)
        if not b:
            continue
        books.append({**b, "rating": ratings.get(bid, 0.0)})
    return {
        "item": {
            "id": str(c.get("collections_id") or ""),
            "userId": str(c.get("users_id") or ""),
            "title": str(c.get("title") or "").strip(),
            "description": str(c.get("description") or "").strip(),
            "isPublic": bool(c.get("is_public")),
            "createdAt": str(c.get("created_at") or _now_iso()),
            "books": books,
            "likeCount": 0,
            "comments": [],
        }
    }
