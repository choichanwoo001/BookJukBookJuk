"""앱 기능·하이브리드 추천(`--supabase-user-id`) 테스트용 Supabase 시드.

생성 항목:
  - public.users (1명)
  - public.shelves (타입별 4개: 평가한 / 읽은 / 읽는중 / 쇼핑리스트)
  - public.shelf_books — **대부분은 `읽은`**에 두고, 나머지 1~2권만 `읽는중`·`쇼핑리스트` (추천·취향 테스트에 유리)
  - public.ratings — **`읽은`에 넣은 책마다 별점** (3.5~5.0 구간을 돌려가며)
  - public.book_user_states — 읽은 책은 REVIEW_POSTED, 읽는 중/찜은 READING·LIST

선행: public.books 에 도서가 있어야 합니다. 없으면 먼저:
  python backend/scripts/seed_hybrid_recommender_e2e.py --isbn 9788937460470 ...

필요: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (권장; RLS 우회)

shelves.user_id 는 `20260414200000_shelves_user_id_varchar.sql` 적용 후 users."Key" 와 동일 문자열입니다.

사용 (저장소 루트):
  python backend/scripts/seed_supabase_app_test_data.py
  python backend/scripts/seed_supabase_app_test_data.py --user-key my_user_1 --isbn 9788937460470 9788936434120
  python backend/scripts/seed_supabase_app_test_data.py --replace
  python backend/scripts/seed_supabase_app_test_data.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
REPO = _SCRIPTS.parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

DEFAULT_USER_KEY = "dev_test_user_1"
DEFAULT_ISBNS = (
    "9788937460470",
    "9788936434120",
)


def _load_env() -> None:
    if not load_dotenv:
        return
    p = REPO / ".env"
    if p.is_file():
        load_dotenv(p)


def _create_client():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
    if not url or not key:
        print(
            "[오류] SUPABASE_URL 및 SUPABASE_SERVICE_ROLE_KEY(또는 ANON) 가 필요합니다.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception as e:
        print(f"[오류] Supabase 클라이언트 생성 실패: {e}", file=sys.stderr)
        raise SystemExit(1)


def _existing_book_ids(supabase, ids: list[str]) -> list[str]:
    if not ids:
        return []
    out: list[str] = []
    for i in range(0, len(ids), 100):
        chunk = ids[i : i + 100]
        res = supabase.table("books").select("id").in_("id", chunk).execute()
        for r in res.data or []:
            bid = str(r.get("id") or "").strip()
            if bid:
                out.append(bid)
    return out


def _resolve_book_ids(supabase, explicit: list[str] | None) -> list[str]:
    """explicit 이 있으면 그 ID 중 books 에 존재하는 것만. 없으면 DB 상위 N권 또는 DEFAULT_ISBNS."""
    if explicit:
        cleaned = [x.strip() for x in explicit if x and str(x).strip()]
        found = _existing_book_ids(supabase, cleaned)
        missing = set(cleaned) - set(found)
        if missing:
            print(f"[WARN] public.books 에 없는 ID 는 제외합니다: {sorted(missing)}")
        return found

    res = supabase.table("books").select("id").limit(16).execute()
    from_db = [str(r["id"]).strip() for r in (res.data or []) if r.get("id")]
    if from_db:
        return from_db

    return _existing_book_ids(supabase, list(DEFAULT_ISBNS))


def _shelf_keys(user_key: str) -> dict[str, str]:
    """shelf_type_enum 값 → shelves."Key" (고정 규칙)."""
    return {
        "평가한": f"{user_key}__shelf_rated",
        "읽은": f"{user_key}__shelf_read",
        "읽는중": f"{user_key}__shelf_reading",
        "쇼핑리스트": f"{user_key}__shelf_wish",
    }


def _delete_user_children(supabase, user_key: str) -> None:
    sk = _shelf_keys(user_key)
    shelf_ids = list(sk.values())

    for i in range(0, len(shelf_ids), 50):
        chunk = shelf_ids[i : i + 50]
        supabase.table("shelf_books").delete().in_("Key2", chunk).execute()

    supabase.table("shelves").delete().eq("user_id", user_key).execute()
    supabase.table("ratings").delete().eq("Key", user_key).execute()
    supabase.table("book_user_states").delete().eq("Key2", user_key).execute()


def run(args: argparse.Namespace) -> None:
    _load_env()
    if args.dry_run:
        print("[dry-run] 쓰기 없음. 아래는 예상 동작입니다.")

    user_key = (args.user_key or DEFAULT_USER_KEY).strip()

    if not user_key:
        print("[오류] --user-key 가 비었습니다.", file=sys.stderr)
        raise SystemExit(1)

    supabase = None if args.dry_run else _create_client()

    if args.dry_run:
        book_ids = [x.strip() for x in (args.isbn or list(DEFAULT_ISBNS)) if x and str(x).strip()]
    else:
        assert supabase is not None
        book_ids = _resolve_book_ids(supabase, args.isbn)

    if len(book_ids) < 1:
        print(
            "[오류] public.books 에 도서가 없고 --isbn 도 비었습니다. "
            "seed_hybrid_recommender_e2e.py 로 books 를 먼저 채우세요.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    sk = _shelf_keys(user_key)

    user_row = {
        "Key": user_key,
        "username": "dev_test_login",
        "password": "dev_test_not_for_prod",
        "nickname": "테스트유저",
        "profile_image_url": None,
        "bio": "seed_supabase_app_test_data.py 로 생성된 테스트 계정",
        "preferred_genres": "소설,에세이",
    }

    shelf_rows = [
        {"Key": sk["평가한"], "user_id": user_key, "shelf_type": "평가한"},
        {"Key": sk["읽은"], "user_id": user_key, "shelf_type": "읽은"},
        {"Key": sk["읽는중"], "user_id": user_key, "shelf_type": "읽는중"},
        {"Key": sk["쇼핑리스트"], "user_id": user_key, "shelf_type": "쇼핑리스트"},
    ]

    # shelf_books: 가능한 한 많이 `읽은`에 둠 (취향·추천 시드 강화). 나머지는 읽는중/찜만 1권씩.
    assignments: list[tuple[str, str]] = []
    n = len(book_ids)
    read_key = sk["읽은"]
    if n <= 2:
        for bid in book_ids:
            assignments.append((bid, read_key))
    elif n == 3:
        assignments.append((book_ids[0], read_key))
        assignments.append((book_ids[1], read_key))
        assignments.append((book_ids[2], sk["쇼핑리스트"]))
    else:
        for i in range(n - 2):
            assignments.append((book_ids[i], read_key))
        assignments.append((book_ids[n - 2], sk["읽는중"]))
        assignments.append((book_ids[n - 1], sk["쇼핑리스트"]))

    read_book_ids = [bid for bid, skey in assignments if skey == read_key]

    rating_rows: list[dict[str, object]] = []
    for j, bid in enumerate(read_book_ids):
        score = 3.5 + (j % 4) * 0.4
        if score > 5.0:
            score = 5.0
        rating_rows.append({"Key": user_key, "Key2": bid, "score": round(score, 1)})

    state_rows: list[dict[str, object]] = []
    for bid, skey in assignments:
        if skey == read_key:
            state_rows.append(
                {"Key2": user_key, "Key": bid, "shelf_state": "REVIEW_POSTED"},
            )
        elif skey == sk["읽는중"]:
            state_rows.append(
                {"Key2": user_key, "Key": bid, "shelf_state": "READING"},
            )
        elif skey == sk["쇼핑리스트"]:
            state_rows.append(
                {"Key2": user_key, "Key": bid, "shelf_state": "LIST"},
            )

    if args.dry_run:
        print(f"user_key={user_key}")
        print(f"books={book_ids}")
        print("users:", user_row)
        print("shelves:", len(shelf_rows), "rows")
        print("shelf_books:", len(assignments), "rows")
        print("ratings:", rating_rows)
        print("book_user_states:", state_rows)
        return

    assert supabase is not None

    if args.replace:
        print(f"[정리] 기존 테스트 데이터 삭제 (user_key={user_key})...")
        _delete_user_children(supabase, user_key)

    supabase.table("users").upsert(user_row, on_conflict="Key").execute()
    print(f"[OK] users upsert: {user_key}")

    for row in shelf_rows:
        supabase.table("shelves").upsert(row, on_conflict="Key").execute()
    print(f"[OK] shelves upsert: {len(shelf_rows)} rows")

    for book_id, shelf_key in assignments:
        supabase.table("shelf_books").upsert(
            {"Key": book_id, "Key2": shelf_key},
            on_conflict="Key,Key2",
        ).execute()
    print(f"[OK] shelf_books upsert: {len(assignments)} rows")

    for r in rating_rows:
        supabase.table("ratings").upsert(r, on_conflict="Key,Key2").execute()
    print(f"[OK] ratings upsert: {len(rating_rows)} rows")

    for s in state_rows:
        supabase.table("book_user_states").upsert(s, on_conflict="Key2,Key").execute()
    print(f"[OK] book_user_states upsert: {len(state_rows)} rows")

    print()
    print("다음으로 하이브리드 추천 CLI 예시:")
    print(
        f'  cd ai && python hybrid_recommender_main.py --use-supabase --persist-kg '
        f'--catalog-isbn {" ".join(book_ids[:3])} --supabase-user-id {user_key}'
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="테스트용 사용자·보관함·별점·서재 상태 시드",
    )
    parser.add_argument(
        "--user-key",
        default=DEFAULT_USER_KEY,
        help=f'public.users."Key" (기본 {DEFAULT_USER_KEY})',
    )
    parser.add_argument(
        "--isbn",
        nargs="+",
        metavar="ISBN",
        help="도서 ID (books.id, 보통 ISBN-13). 여러 권 넣을수록 읽은 책·별점 시드가 많아져 추천 테스트에 유리. "
        "생략 시 DB books 에서 최대 16권 또는 기본 ISBN 목록 시도",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="동일 user-key 의 shelves/shelf_books/ratings/book_user_states 를 지운 뒤 다시 삽입",
    )
    parser.add_argument("--dry-run", action="store_true", help="Supabase 쓰기 없음")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
