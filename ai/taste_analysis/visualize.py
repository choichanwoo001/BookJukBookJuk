import platform

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from sklearn.decomposition import PCA

from .library_api import BookInfo
from .clustering import TasteCluster

CLUSTER_COLORS = [
    "#4E79A7", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F",
]


def _setup_korean_font():
    system = platform.system()
    if system == "Windows":
        candidates = ["Malgun Gothic", "맑은 고딕"]
    elif system == "Darwin":
        candidates = ["AppleGothic", "Apple SD Gothic Neo"]
    else:
        candidates = ["NanumGothic", "NanumBarunGothic"]

    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break

    plt.rcParams["axes.unicode_minus"] = False


OUTLIER_COLOR = "#888888"


def visualize_clusters(
    book_vector_pairs: list[tuple[BookInfo, np.ndarray]],
    clusters: list[TasteCluster],
    outliers: list[BookInfo] | None = None,
    save_path: str | None = "cluster_result.png",
    show: bool = True,
):
    _setup_korean_font()

    outliers = outliers or []
    outlier_isbns = {b.isbn13 for b in outliers}

    books = [b for b, _ in book_vector_pairs]
    vectors = np.stack([v for _, v in book_vector_pairs])

    label_map: dict[str, int] = {}
    for cluster in clusters:
        for book in cluster.books:
            label_map[book.isbn13] = cluster.label

    # -1 for outliers so they're not in any cluster color
    labels = [label_map.get(b.isbn13, -1) if b.isbn13 not in outlier_isbns else -1 for b in books]

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(vectors)
    var_ratio = pca.explained_variance_ratio_

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    for cluster in clusters:
        mask = [i for i, b in enumerate(books) if label_map.get(b.isbn13) == cluster.label]
        if not mask:
            continue
        color = CLUSTER_COLORS[cluster.label % len(CLUSTER_COLORS)]
        top_kw = ", ".join(w for w, _ in cluster.top_keywords[:3])
        group_label = f"그룹 {cluster.label + 1}: {top_kw}"

        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            c=color,
            s=200,
            alpha=0.85,
            edgecolors="white",
            linewidths=1.5,
            label=group_label,
            zorder=3,
        )

    # 아웃라이어 점 (회색)
    outlier_mask = [i for i, b in enumerate(books) if b.isbn13 in outlier_isbns]
    if outlier_mask:
        ax.scatter(
            coords[outlier_mask, 0],
            coords[outlier_mask, 1],
            c=OUTLIER_COLOR,
            s=200,
            alpha=0.85,
            edgecolors="white",
            linewidths=1.5,
            label="아웃라이어",
            zorder=3,
        )

    for i, book in enumerate(books):
        color = OUTLIER_COLOR if labels[i] == -1 else CLUSTER_COLORS[labels[i] % len(CLUSTER_COLORS)]
        title = book.title if len(book.title) <= 12 else book.title[:11] + "…"
        ax.annotate(
            title,
            (coords[i, 0], coords[i, 1]),
            textcoords="offset points",
            xytext=(0, 13),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=color,
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="white",
                edgecolor=color,
                alpha=0.9,
            ),
            zorder=4,
        )

    if len(clusters) > 1:
        for cluster in clusters:
            mask = [i for i, b in enumerate(books) if label_map.get(b.isbn13) == cluster.label]
            if len(mask) >= 2:
                cx = coords[mask, 0].mean()
                cy = coords[mask, 1].mean()
                color = CLUSTER_COLORS[cluster.label % len(CLUSTER_COLORS)]
                ax.plot(cx, cy, marker="X", markersize=14, color=color,
                        markeredgecolor="white", markeredgewidth=2, zorder=5)

    ax.set_xlabel(f"PCA 1 (설명력 {var_ratio[0]:.1%})", fontsize=11)
    ax.set_ylabel(f"PCA 2 (설명력 {var_ratio[1]:.1%})", fontsize=11)
    ax.set_title("독서 취향 클러스터링 결과", fontsize=16, fontweight="bold", pad=15)

    ax.legend(
        loc="upper left",
        fontsize=9,
        framealpha=0.9,
        edgecolor="#CCCCCC",
    )

    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"  → 시각화 저장: {save_path}")

    if show:
        plt.show()

    plt.close(fig)
