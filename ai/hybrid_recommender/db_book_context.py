"""books.db 행으로 BookContext를 구성해 API 호출 없이 파이프라인에 넣는다."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from book_chat.data_collector import BookContext
from book_seeder import db as book_db
from taste_analysis.library_api import BookKeyword

from .sqlite_catalog import resolve_books_db_path


def book_context_from_db(isbn13: str, db_path: str | None = None) -> BookContext | None:
    """ISBN이 `books`에 있으면 키워드·raw_docs를 붙여 BookContext를 만든다. 없으면 None."""
    path = resolve_books_db_path(db_path)
    if not os.path.isfile(path):
        return None

    book_db.create_schema(path)
    with book_db.get_conn(path) as conn:
        cur = conn.execute(
            """
            SELECT isbn13, title, authors, publisher, published_year,
                   COALESCE(description, ''), COALESCE(author_bio, '') AS author_bio,
                   COALESCE(editorial_review, '') AS editorial_review,
                   kdc_class_no, kdc_class_nm,
                   COALESCE(wiki_book_summary, ''), COALESCE(wiki_author_summary, '')
            FROM books WHERE isbn13 = ?
            """,
            (isbn13,),
        )
        row = cur.fetchone()
        if not row:
            return None

        (
            isbn,
            title,
            authors,
            publisher,
            published_year,
            description,
            author_bio,
            editorial_review,
            kdc_no,
            kdc_nm,
            wiki_book,
            wiki_author,
        ) = row

        cur = conn.execute(
            "SELECT word, weight FROM book_keywords WHERE isbn13 = ? ORDER BY weight DESC",
            (isbn13,),
        )
        keywords = [BookKeyword(word=w, weight=float(weight)) for w, weight in cur.fetchall()]

        cur = conn.execute(
            "SELECT doc_type, source, section_title, text FROM book_raw_docs WHERE isbn13 = ?",
            (isbn13,),
        )
        raw_docs: list[dict] = []
        for doc_type, source, section_title, text in cur.fetchall():
            raw_docs.append(
                {
                    "doc_type": doc_type or "",
                    "source": source or "",
                    "section_title": section_title,
                    "text": text or "",
                }
            )

    kdc = ""
    if kdc_nm:
        kdc = f"{kdc_no} {kdc_nm}".strip() if kdc_no else str(kdc_nm)
    elif kdc_no:
        kdc = str(kdc_no)

    return BookContext(
        isbn13=isbn,
        title=title or "",
        authors=authors or "",
        publisher=publisher or "",
        published_year=published_year or "",
        description=description,
        author_bio=author_bio or "",
        editorial_review=editorial_review or "",
        keywords=keywords,
        subject_names=[],
        kdc_class=kdc,
        wiki_book_summary=wiki_book or "",
        wiki_author_summary=wiki_author or "",
        wiki_extra_sections=[],
        raw_docs=raw_docs,
    )
