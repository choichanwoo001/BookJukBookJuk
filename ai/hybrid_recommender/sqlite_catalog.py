"""books.db에서 카탈로그 ISBN·사용자 독서 이력을 읽는다."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from book_seeder import db as book_db


@dataclass
class UserReadRecord:
    isbn13: str
    title: str
    occurred_at: datetime
    rating: float | None


def resolve_books_db_path(explicit: str | None = None) -> str:
    """환경변수 BOOKS_DB_PATH 또는 book_seeder 기본 경로."""
    if explicit and explicit.strip():
        return os.path.abspath(explicit.strip())
    env = os.getenv("BOOKS_DB_PATH", "").strip()
    if env:
        return os.path.abspath(env)
    return book_db.DB_PATH


def list_catalog_isbns(
    db_path: str | None = None,
    sector: int | None = None,
    limit: int | None = None,
) -> list[str]:
    """추천 후보로 쓸 ISBN 목록."""
    path = resolve_books_db_path(db_path)
    book_db.create_schema(path)
    q = "SELECT isbn13 FROM books"
    params: list = []
    if sector is not None:
        q += " WHERE sector = ?"
        params.append(sector)
    q += " ORDER BY isbn13"
    if limit is not None and limit > 0:
        q += " LIMIT ?"
        params.append(limit)

    with book_db.get_conn(path) as conn:
        cur = conn.execute(q, params)
        return [row[0] for row in cur.fetchall()]


def load_user_read_actions(
    user_id: str,
    db_path: str | None = None,
    action_type: str = "read_complete",
) -> list[UserReadRecord]:
    """users + books JOIN으로 독서 이력을 불러온다."""
    path = resolve_books_db_path(db_path)
    book_db.create_schema(path)
    with book_db.get_conn(path) as conn:
        cur = conn.execute(
            """
            SELECT u.isbn13, b.title, u.occurred_at, u.rating
            FROM user_book_actions AS u
            INNER JOIN books AS b ON b.isbn13 = u.isbn13
            WHERE u.user_id = ? AND u.action_type = ?
            ORDER BY u.occurred_at ASC
            """,
            (user_id, action_type),
        )
        rows: list[UserReadRecord] = []
        for isbn13, title, occurred_at, rating in cur.fetchall():
            ts = _parse_iso_datetime(str(occurred_at))
            rows.append(
                UserReadRecord(
                    isbn13=isbn13,
                    title=title or "",
                    occurred_at=ts,
                    rating=float(rating) if rating is not None else None,
                )
            )
        return rows


def _parse_iso_datetime(s: str) -> datetime:
    """SQLite에 저장된 ISO 문자열을 timezone-aware datetime으로."""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        from datetime import timezone

        dt = dt.replace(tzinfo=timezone.utc)
    return dt
