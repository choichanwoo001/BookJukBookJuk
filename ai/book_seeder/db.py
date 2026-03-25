"""SQLite DB 연결, 스키마 생성, upsert 함수."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "books.db",
)

_DDL = """
CREATE TABLE IF NOT EXISTS books (
    isbn13           TEXT    NOT NULL PRIMARY KEY,
    isbn10           TEXT    NULL,
    title            TEXT    NOT NULL,
    authors          TEXT    NOT NULL DEFAULT '',
    publisher        TEXT    NOT NULL DEFAULT '',
    published_year   TEXT    NOT NULL DEFAULT '',
    description      TEXT    NULL,
    author_bio       TEXT    NULL,
    editorial_review TEXT    NULL,
    kdc_class_no     TEXT    NOT NULL DEFAULT '',
    kdc_class_nm     TEXT    NOT NULL DEFAULT '',
    sector           INTEGER NOT NULL,
    wiki_book_summary    TEXT NULL,
    wiki_author_summary  TEXT NULL,
    wiki_lang        TEXT    NULL,
    cover_image_url  TEXT    NULL,
    is_korean_author INTEGER NOT NULL DEFAULT 0,
    is_recent        INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_books_sector         ON books(sector);
CREATE INDEX IF NOT EXISTS idx_books_korean_recent  ON books(is_korean_author, is_recent);

CREATE TABLE IF NOT EXISTS book_keywords (
    id     INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    isbn13 TEXT    NOT NULL,
    word   TEXT    NOT NULL,
    weight REAL    NOT NULL DEFAULT 0.0,
    FOREIGN KEY (isbn13) REFERENCES books(isbn13) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_keywords_isbn13 ON book_keywords(isbn13);

CREATE TABLE IF NOT EXISTS book_raw_docs (
    id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    isbn13        TEXT    NOT NULL,
    doc_type      TEXT    NOT NULL,
    source        TEXT    NOT NULL,
    section_title TEXT    NULL,
    text          TEXT    NOT NULL,
    FOREIGN KEY (isbn13) REFERENCES books(isbn13) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_raw_docs_isbn13 ON book_raw_docs(isbn13);
"""

_DROP_DDL = """
DROP TABLE IF EXISTS book_raw_docs;
DROP TABLE IF EXISTS book_keywords;
DROP TABLE IF EXISTS books;
"""


@dataclass
class BookRow:
    isbn13: str
    isbn10: str | None
    title: str
    authors: str
    publisher: str
    published_year: str
    description: str
    author_bio: str
    editorial_review: str
    kdc_class_no: str
    kdc_class_nm: str
    sector: int
    wiki_book_summary: str
    wiki_author_summary: str
    wiki_lang: str | None
    cover_image_url: str | None
    is_korean_author: bool
    is_recent: bool


@contextmanager
def get_conn(db_path: str = DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_schema(db_path: str = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(_DDL)


def reset_schema(db_path: str = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(_DROP_DDL)


def isbn_exists(isbn13: str, db_path: str = DB_PATH) -> bool:
    with get_conn(db_path) as conn:
        cur = conn.execute("SELECT 1 FROM books WHERE isbn13 = ?", (isbn13,))
        return cur.fetchone() is not None


def count_sector(sector: int, db_path: str = DB_PATH) -> int:
    with get_conn(db_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM books WHERE sector = ?", (sector,))
        return cur.fetchone()[0]


def count_korean_recent(db_path: str = DB_PATH) -> int:
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "SELECT COUNT(*) FROM books WHERE is_korean_author=1 AND is_recent=1"
        )
        return cur.fetchone()[0]


def count_korean_recent_by_sector(db_path: str = DB_PATH) -> dict[int, int]:
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "SELECT sector, COUNT(*) FROM books "
            "WHERE is_korean_author=1 AND is_recent=1 GROUP BY sector"
        )
        return {row[0]: row[1] for row in cur.fetchall()}


def get_sector_stats(db_path: str = DB_PATH) -> list[dict]:
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "SELECT sector, COUNT(*) AS total, "
            "SUM(is_korean_author) AS korean, "
            "SUM(is_recent) AS recent, "
            "SUM(is_korean_author AND is_recent) AS korean_recent "
            "FROM books GROUP BY sector ORDER BY sector"
        )
        return [
            {
                "sector": row[0],
                "total": row[1],
                "korean": row[2],
                "recent": row[3],
                "korean_recent": row[4],
            }
            for row in cur.fetchall()
        ]


def upsert_book(row: BookRow, db_path: str = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO books (
                isbn13, isbn10, title, authors, publisher, published_year,
                description, author_bio, editorial_review,
                kdc_class_no, kdc_class_nm, sector,
                wiki_book_summary, wiki_author_summary, wiki_lang,
                cover_image_url, is_korean_author, is_recent
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(isbn13) DO UPDATE SET
                title=excluded.title,
                authors=excluded.authors,
                publisher=excluded.publisher,
                published_year=excluded.published_year,
                description=excluded.description,
                author_bio=excluded.author_bio,
                editorial_review=excluded.editorial_review,
                kdc_class_no=excluded.kdc_class_no,
                kdc_class_nm=excluded.kdc_class_nm,
                sector=excluded.sector,
                wiki_book_summary=excluded.wiki_book_summary,
                wiki_author_summary=excluded.wiki_author_summary,
                wiki_lang=excluded.wiki_lang,
                cover_image_url=excluded.cover_image_url,
                is_korean_author=excluded.is_korean_author,
                is_recent=excluded.is_recent
            """,
            (
                row.isbn13, row.isbn10, row.title, row.authors,
                row.publisher, row.published_year,
                row.description, row.author_bio, row.editorial_review,
                row.kdc_class_no, row.kdc_class_nm, row.sector,
                row.wiki_book_summary, row.wiki_author_summary, row.wiki_lang,
                row.cover_image_url,
                int(row.is_korean_author), int(row.is_recent),
            ),
        )


def insert_keywords(isbn13: str, keywords: list, db_path: str = DB_PATH) -> None:
    if not keywords:
        return
    with get_conn(db_path) as conn:
        conn.execute("DELETE FROM book_keywords WHERE isbn13 = ?", (isbn13,))
        conn.executemany(
            "INSERT INTO book_keywords (isbn13, word, weight) VALUES (?,?,?)",
            [(isbn13, kw.word, float(kw.weight)) for kw in keywords],
        )


def insert_raw_docs(isbn13: str, raw_docs: list[dict], db_path: str = DB_PATH) -> None:
    if not raw_docs:
        return
    with get_conn(db_path) as conn:
        conn.execute("DELETE FROM book_raw_docs WHERE isbn13 = ?", (isbn13,))
        conn.executemany(
            "INSERT INTO book_raw_docs (isbn13, doc_type, source, section_title, text) "
            "VALUES (?,?,?,?,?)",
            [
                (
                    isbn13,
                    d.get("doc_type", ""),
                    d.get("source", ""),
                    d.get("section_title"),
                    d.get("text", ""),
                )
                for d in raw_docs
            ],
        )
