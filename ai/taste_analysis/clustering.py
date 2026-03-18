from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score

from .library_api import BookInfo


@dataclass
class TasteCluster:
    label: int
    books: list[BookInfo]
    top_keywords: list[tuple[str, float]]
    kdc_distribution: dict[str, int]


def find_optimal_k(vectors: np.ndarray, max_k: int | None = None) -> int:
    n = len(vectors)
    if n <= 2:
        return 1

    if max_k is None:
        max_k = min(5, max(3, n // 10))  # 데이터 양에 따라 3~5까지 유연하게
    max_k = min(max_k, n - 1)
    best_k = 1
    best_score = -1.0

    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(vectors)

        if len(set(labels)) < 2:
            continue

        score = silhouette_score(vectors, labels)
        print(f"  [K-means] K={k}, silhouette={score:.3f}")
        if score > best_score:
            best_score = score
            best_k = k

    # 0.05 이상이면 의미 있는 분리로 판단
    if best_score < 0.05:
        return 1

    return best_k


def _cluster_dbscan(
    vectors: np.ndarray,
    eps: float = 0.45,
    min_samples: int = 2,
) -> np.ndarray:
    """DBSCAN으로 클러스터링. 반환: labels (-1 = 노이즈/아웃라이어)."""
    # 벡터가 이미 정규화되어 있으므로 cosine 거리 사용
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine", n_jobs=-1)
    return clustering.fit_predict(vectors)


def cluster_books(
    book_vector_pairs: list[tuple[BookInfo, np.ndarray]],
    min_cluster_size: int = 2,
    distance_outlier_percentile: float = 95.0,
    method: str = "kmeans",
    dbscan_eps: float = 0.45,
    dbscan_min_samples: int = 2,
    kmeans_max_k: int | None = None,
) -> tuple[list[TasteCluster], list[BookInfo]]:
    """클러스터링 후 아웃라이어를 분리해 반환합니다.

    method:
      - "kmeans": K를 실루엣으로 결정, 이후 작은 클러스터·거리 기반 아웃라이어 제거.
      - "dbscan": 밀도 기반 클러스터링, 노이즈를 아웃라이어로 반환 (K 불필요).

    아웃라이어 (K-means):
    1) 최소 클러스터 크기 미만(기본 2권 미만)이면 해당 클러스터 전체를 아웃라이어로 처리.
    2) 각 클러스터 내에서 중심으로부터의 거리가 percentile(기본 95%) 초과인 점도 아웃라이어로 처리.
    """
    if not book_vector_pairs:
        return [], []

    books = [b for b, _ in book_vector_pairs]
    vectors = np.stack([v for _, v in book_vector_pairs])

    if method == "dbscan":
        labels = _cluster_dbscan(vectors, eps=dbscan_eps, min_samples=dbscan_min_samples)
        labels = labels.tolist()
        # DBSCAN: -1이 노이즈, 나머지는 클러스터 ID
        cluster_map: dict[int, list[int]] = defaultdict(list)
        for i, label in enumerate(labels):
            if label >= 0:
                cluster_map[label].append(i)
        outlier_indices = {i for i, label in enumerate(labels) if label == -1}
        # DBSCAN은 이미 노이즈를 구분했으므로 거리 기반 아웃라이어 스텝 생략
        distance_outlier_percentile = 100
    else:
        k = find_optimal_k(vectors, max_k=kmeans_max_k)
        if k == 1:
            labels = [0] * len(books)
        else:
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(vectors)
            labels = labels.tolist()

        cluster_map = defaultdict(list)
        for i, label in enumerate(labels):
            cluster_map[label].append(i)
        outlier_indices = set()

        # 1) 너무 작은 클러스터는 전부 아웃라이어
        for label in list(cluster_map.keys()):
            if len(cluster_map[label]) < min_cluster_size:
                outlier_indices.update(cluster_map[label])
                del cluster_map[label]

        # 2) 각 클러스터 내 거리 기반 아웃라이어 (중심에서 너무 먼 점)
        if cluster_map and distance_outlier_percentile < 100:
            for label, indices in cluster_map.items():
                if len(indices) < 2:
                    continue
                sub_vectors = vectors[indices]
                centroid = sub_vectors.mean(axis=0)
                distances = np.linalg.norm(sub_vectors - centroid, axis=1)
                threshold = np.percentile(distances, distance_outlier_percentile)
                for j, idx in enumerate(indices):
                    if distances[j] > threshold:
                        outlier_indices.add(idx)

    for label in cluster_map:
        cluster_map[label] = [i for i in cluster_map[label] if i not in outlier_indices]
    cluster_map = {lbl: idx_list for lbl, idx_list in cluster_map.items() if idx_list}

    # 레이블 재부여 0, 1, 2, ...
    clusters: list[TasteCluster] = []
    for new_label, (_, indices) in enumerate(sorted(cluster_map.items())):
        cluster_books_list = [books[i] for i in indices]
        top_kw = _extract_top_keywords(cluster_books_list, top_n=10)
        kdc_dist = _extract_kdc_distribution(cluster_books_list)
        clusters.append(
            TasteCluster(
                label=new_label,
                books=cluster_books_list,
                top_keywords=top_kw,
                kdc_distribution=kdc_dist,
            )
        )

    outliers = [books[i] for i in sorted(outlier_indices)]
    return clusters, outliers


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
