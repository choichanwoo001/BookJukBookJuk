import asyncio
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from openai import AsyncOpenAI

from taste_analysis import (
    BookInfo,
    fetch_books_parallel,
    fetch_random_books,
    build_all_book_vectors,
    cluster_books,
    analyze_taste,
    visualize_clusters,
)

load_dotenv()

# .env 에서 읽음: LIBRARY_API_KEY(정보나루), OPENAI_API_KEY
LIBRARY_API_KEY = os.getenv("LIBRARY_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def print_book_summary(books: list[BookInfo]):
    print(f"{'━' * 60}")
    for i, book in enumerate(books, 1):
        kw_count = len(book.keywords)
        print(f"  [{i:2d}] {book.title}  (키워드 {kw_count}개)")
    print(f"{'━' * 60}")


def _print_cluster_summary(clusters: list, outliers: list[BookInfo]):
    if outliers:
        print(f"  아웃라이어: {', '.join(b.title for b in outliers)}")
    for i, c in enumerate(clusters):
        titles = ", ".join(b.title for b in c.books)
        kw_preview = ", ".join(w for w, _ in c.top_keywords[:5])
        kdc_preview = ", ".join(f"{n}({cnt})" for n, cnt in c.kdc_distribution.items())
        print(f"  그룹 {i + 1}: [{titles}]")
        print(f"    키워드: {kw_preview}")
        print(f"    분류: {kdc_preview}")


async def _run_compare_mode(openai_client, book_vectors) -> str:
    """K-means와 DBSCAN을 둘 다 실행해 결과를 비교합니다."""
    results: list[str] = []

    for method, save_name in [("kmeans", "cluster_result_kmeans.png"), ("dbscan", "cluster_result_dbscan.png")]:
        print(f"\n[STEP 3] 클러스터링 — {method.upper()}...")
        t2 = time.time()
        clusters, outliers = cluster_books(book_vectors, method=method)
        print(f"  → {len(clusters)}개 취향 그룹, 아웃라이어 {len(outliers)}권 ({time.time() - t2:.1f}s)")
        _print_cluster_summary(clusters, outliers)

        print(f"\n[STEP 3.5] 시각화 저장: {save_name}")
        visualize_clusters(book_vectors, clusters, outliers=outliers, save_path=save_name, show=False)

        if clusters:
            print(f"\n[STEP 4] LLM 취향 분석 ({method.upper()} 기준)...")
            t3 = time.time()
            analysis = await analyze_taste(openai_client, clusters)
            print(f"  → 완료 ({time.time() - t3:.1f}s)")
            results.append(f"[{method.upper()} 기반 분석]\n{analysis}")
        else:
            results.append(f"[{method.upper()} 기반 분석]\n(클러스터가 없어 분석을 건너뜁니다.)")

    return "\n\n" + "─" * 50 + "\n\n".join(results)


async def analyze_reading_taste(
    isbn_list: list[str] | None = None,
    random_mode: bool = False,
    compare_mode: bool = False,
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    # STEP 1: 데이터 수집
    t0 = time.time()
    if random_mode:
        print("[STEP 1] 정보나루에서 랜덤 50권 수집 중...")
        books = await fetch_random_books(LIBRARY_API_KEY, count=50)
    else:
        print(f"[STEP 1] {len(isbn_list)}권의 키워드 병렬 수집 중...")
        books = await fetch_books_parallel(LIBRARY_API_KEY, isbn_list)

    books = [b for b in books if b.keywords and b.title]
    print(f"  → {len(books)}권 수집 완료 ({time.time() - t0:.1f}s)")

    if not books:
        return (
            "키워드를 가져올 수 있는 책이 없습니다.\n"
            "위 [WARN] 메시지가 있다면 그 내용대로 조치하세요 (예: 정보나루 IP 등록, 일일 한도). "
            "키가 없다면 .env에 LIBRARY_API_KEY를 넣고, 발급: https://www.data4library.kr/"
        )

    print_book_summary(books)

    # STEP 2: 키워드 임베딩
    print(f"\n[STEP 2] 키워드 임베딩 생성 중...")
    t1 = time.time()
    book_vectors = await build_all_book_vectors(openai_client, books)
    print(f"  → {len(book_vectors)}권 벡터 생성 완료 ({time.time() - t1:.1f}s)")

    if not book_vectors:
        return "벡터를 생성할 수 있는 책이 없습니다."

    if compare_mode:
        return await _run_compare_mode(openai_client, book_vectors)

    # STEP 3: 클러스터링 (단일 방법)
    clustering_method = os.getenv("CLUSTERING_METHOD", "kmeans").strip().lower()
    if clustering_method not in ("kmeans", "dbscan"):
        clustering_method = "kmeans"
    print(f"\n[STEP 3] 클러스터링 (취향 분리) — {clustering_method.upper()}...")
    t2 = time.time()
    clusters, outliers = cluster_books(
        book_vectors,
        method=clustering_method,
    )
    print(f"  → {len(clusters)}개 취향 그룹, 아웃라이어 {len(outliers)}권 ({time.time() - t2:.1f}s)")

    if outliers:
        print(f"  아웃라이어: {', '.join(b.title for b in outliers)}")

    for i, c in enumerate(clusters):
        titles = ", ".join(b.title for b in c.books)
        kw_preview = ", ".join(w for w, _ in c.top_keywords[:5])
        kdc_preview = ", ".join(f"{n}({cnt})" for n, cnt in c.kdc_distribution.items())
        print(f"  그룹 {i + 1}: [{titles}]")
        print(f"    키워드: {kw_preview}")
        print(f"    분류: {kdc_preview}")

    # STEP 3.5: 클러스터링 시각화
    print(f"\n[STEP 3.5] 클러스터링 시각화...")
    visualize_clusters(book_vectors, clusters, outliers=outliers, save_path="cluster_result.png", show=False)

    # STEP 4: LLM 취향 분석
    print(f"\n[STEP 4] LLM 취향 분석 중...")
    t3 = time.time()
    result = await analyze_taste(openai_client, clusters)
    print(f"  → 분석 완료 ({time.time() - t3:.1f}s)")

    return result


async def main():
    argv = [a for a in sys.argv[1:] if a != "--compare"]
    compare_mode = "--compare" in sys.argv[1:]
    random_mode = "--random" in sys.argv[1:] or len(argv) == 0
    isbn_list = None if random_mode else [a for a in argv if not a.startswith("--")]

    print("=" * 60)
    print("  독서 취향 분석기")
    print("=" * 60)
    if compare_mode:
        print("모드: K-means vs DBSCAN 결과 비교\n")
    elif random_mode:
        print("모드: 랜덤 50권 자동 선택\n")
    else:
        print(f"분석 대상: {len(isbn_list)}권\n")

    result = await analyze_reading_taste(
        isbn_list=isbn_list,
        random_mode=random_mode,
        compare_mode=compare_mode,
    )

    print("\n" + "=" * 60)
    print("  분석 결과")
    print("=" * 60)
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
