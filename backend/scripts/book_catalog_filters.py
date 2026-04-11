"""booksCatalog / DB 행에서 어린이·교육용 도서를 걸러내기 위한 공통 규칙.

KDC 경로·표제·출판사 등을 조합한다. (완벽한 분류가 아니라 카탈로그 시드용 휴리스틱)
"""
from __future__ import annotations

import re


def _norm(s: str) -> str:
    return (s or "").strip()


def is_education_book(kdc_nm: str, title: str, description: str) -> bool:
    """교육학 분류, 학습·교과·시험 위주 도서."""
    k = _norm(kdc_nm)
    parts = [p.strip() for p in k.split(">") if p.strip()]
    if "교육학" in parts:
        return True
    t = _norm(title)
    d = _norm(description)
    blob = f"{t} {d}"
    edu_title = (
        "학습만화",
        "교과서",
        "참고서",
        "문제집",
        "수능",
        "수험",
        "EBS",
        "초등과학",
        "초등국어",
        "개념잡기",
        "실력완성",
        "평가문제",
        "전국연합",
    )
    if any(x in blob for x in edu_title):
        return True
    if re.search(r"\bWhy\?\s*초등", blob):
        return True
    return False


def is_children_book(kdc_nm: str, title: str, publisher: str, description: str) -> bool:
    """어린이·유아·그림책·아동 대상 위주."""
    k = _norm(kdc_nm)
    t = _norm(title)
    p = _norm(publisher)
    d = _norm(description)

    child_in_kdc = (
        "아동문학",
        "어린이",
        "유아",
        "초등교육",
        "청소년문학",
        "그림책",
    )
    for phrase in child_in_kdc:
        if phrase in k:
            return True

    blob = f"{t} {d} {p}"
    child_blob = (
        "그림책",
        "유아",
        "어린이",
        "초등학교",
        "주니어",
        "토토북",
        "어린이과학동아",
        "인문학동화",
        "아기 ",
    )
    if any(x in blob for x in child_blob):
        return True
    if "주니어" in p or "(주니어)" in t:
        return True
    return False


def should_keep_book(row: dict) -> bool:
    """어린이·교육용이 아니면 True."""
    kdc_nm = str(row.get("kdc_class_nm") or "")
    title = str(row.get("title") or "")
    publisher = str(row.get("publisher") or "")
    description = str(row.get("description") or "")

    if is_education_book(kdc_nm, title, description):
        return False
    if is_children_book(kdc_nm, title, publisher, description):
        return False
    return True


def pick_per_sector(rows: list[dict], per_sector: int = 50) -> list[dict]:
    """sector(0~9)별로 최대 per_sector권, id 기준 정렬."""
    by_sector: dict[int, list[dict]] = {i: [] for i in range(10)}
    for r in rows:
        try:
            s = int(r.get("sector") or 0)
        except (TypeError, ValueError):
            s = 0
        if 0 <= s <= 9:
            by_sector[s].append(r)

    out: list[dict] = []
    for s in range(10):
        chunk = sorted(by_sector[s], key=lambda x: str(x.get("id") or ""))
        out.extend(chunk[:per_sector])
    return out
