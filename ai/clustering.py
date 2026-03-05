from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from library_api import BookInfo


@dataclass
class TasteCluster:
    label: int
    books: list[BookInfo]
    top_keywords: list[tuple[str, float]]
    kdc_distribution: dict[str, int]


def find_optimal_k(vectors: np.ndarray, max_k: int = 3) -> int:
    n = len(vectors)
    if n <= 2:
        return 1

    max_k = min(max_k, n - 1)
    best_k = 1
    best_score = -1.0

    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(vectors)

        if len(set(labels)) < 2:
            continue

        score = silhouette_score(vectors, labels)
        print(f"  [클러스터링] K={k}, silhouette={score:.3f}")
        if score > best_score:
            best_score = score
            best_k = k

    # 0.05 이상이면 의미 있는 분리로 판단
    if best_score < 0.05:
        return 1

    return best_k


def cluster_books(
    book_vector_pairs: list[tuple[BookInfo, np.ndarray]],
) -> list[TasteCluster]:
    if not book_vector_pairs:
        return []

    books = [b for b, _ in book_vector_pairs]
    vectors = np.stack([v for _, v in book_vector_pairs])

    k = find_optimal_k(vectors)

    if k == 1:
        labels = [0] * len(books)
    else:
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(vectors).tolist()

    cluster_map: dict[int, list[BookInfo]] = defaultdict(list)
    for book, label in zip(books, labels):
        cluster_map[label].append(book)

    clusters: list[TasteCluster] = []
    for label, cluster_books_list in sorted(cluster_map.items()):
        top_kw = _extract_top_keywords(cluster_books_list, top_n=10)
        kdc_dist = _extract_kdc_distribution(cluster_books_list)
        clusters.append(
            TasteCluster(
                label=label,
                books=cluster_books_list,
                top_keywords=top_kw,
                kdc_distribution=kdc_dist,
            )
        )

    return clusters


def _extract_top_keywords(
    books: list[BookInfo],
    top_n: int = 10,
) -> list[tuple[str, float]]:
    word_score: dict[str, float] = defaultdict(float)
    for book in books:
        for kw in book.keywords:
            word_score[kw.word] += kw.weight

    sorted_words = sorted(word_score.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:top_n]


def _extract_kdc_distribution(books: list[BookInfo]) -> dict[str, int]:
    dist: dict[str, int] = defaultdict(int)
    for book in books:
        name = book.class_nm.strip() if book.class_nm else "미분류"
        if not name:
            name = "미분류"
        dist[name] += 1
    return dict(sorted(dist.items(), key=lambda x: x[1], reverse=True))
