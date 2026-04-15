"""
사용자 독서 취향 분석 모듈.
- library_api: 정보나루 API 연동 (도서/키워드)
- embedding: 키워드 임베딩
- clustering: 취향 클러스터링
- taste_analyzer: LLM 취향 분석
- visualize: 클러스터 시각화

library_api만 쓰는 스크립트는 clustering/numpy 등을 불러오지 않도록,
무거운 서브모듈은 지연 로딩합니다.
"""

from __future__ import annotations

from typing import Any

from .library_api import (
    BookInfo,
    BookKeyword,
    fetch_books_parallel,
    fetch_random_books,
)

__all__ = [
    "BookInfo",
    "BookKeyword",
    "TasteCluster",
    "fetch_books_parallel",
    "fetch_random_books",
    "build_all_book_vectors",
    "cluster_books",
    "analyze_taste",
    "visualize_clusters",
]


def __getattr__(name: str) -> Any:
    if name == "TasteCluster":
        from .clustering import TasteCluster

        return TasteCluster
    if name == "cluster_books":
        from .clustering import cluster_books

        return cluster_books
    if name == "build_all_book_vectors":
        from .embedding import build_all_book_vectors

        return build_all_book_vectors
    if name == "analyze_taste":
        from .taste_analyzer import analyze_taste

        return analyze_taste
    if name == "visualize_clusters":
        from .visualize import visualize_clusters

        return visualize_clusters
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
