"""Export books.db rows to frontend/src/data/booksCatalog.json for the React app."""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "books.db")
OUT_PATH = os.path.join(
    os.path.dirname(ROOT),
    "frontend",
    "src",
    "data",
    "booksCatalog.json",
)


def main() -> int:
    if not os.path.isfile(DB_PATH):
        print(f"Missing DB: {DB_PATH}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        """
        SELECT
          isbn13 AS id,
          COALESCE(NULLIF(TRIM(title), ''), isbn13) AS title,
          COALESCE(NULLIF(TRIM(authors), ''), '') AS authors,
          COALESCE(NULLIF(TRIM(description), ''), '') AS description,
          COALESCE(NULLIF(TRIM(author_bio), ''), '') AS author_bio,
          COALESCE(NULLIF(TRIM(editorial_review), ''), '') AS editorial_review,
          COALESCE(NULLIF(TRIM(publisher), ''), '') AS publisher,
          COALESCE(NULLIF(TRIM(published_year), ''), '') AS published_year,
          COALESCE(NULLIF(TRIM(kdc_class_no), ''), '') AS kdc_class_no,
          COALESCE(NULLIF(TRIM(kdc_class_nm), ''), '') AS kdc_class_nm,
          sector,
          COALESCE(NULLIF(TRIM(cover_image_url), ''), '') AS cover_image_url
        FROM books
        ORDER BY isbn13
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    with_cover = sum(1 for r in rows if r.get("cover_image_url"))
    print(f"Wrote {len(rows)} books ({with_cover} with cover) -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
