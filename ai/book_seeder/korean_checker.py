"""한국 저자 여부 및 최근 출판 여부 판별."""
from __future__ import annotations

import re

from .wiki_checker import parse_primary_author

_HANGUL_RE = re.compile(r"[가-힣]")


def is_korean_author(authors_str: str) -> bool:
    """주 저자 이름에 한글이 포함되어 있으면 한국 저자로 간주."""
    name = parse_primary_author(authors_str)
    return bool(_HANGUL_RE.search(name))


def is_recent(published_year: str) -> bool:
    """published_year가 4자리 연도이고 2020 이상이면 최근 도서."""
    return bool(
        published_year
        and len(published_year) == 4
        and published_year.isdigit()
        and published_year >= "2020"
    )
