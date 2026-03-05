import asyncio
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from openai import AsyncOpenAI

from library_api import fetch_books_parallel, fetch_random_books, BookInfo
from embedding import build_all_book_vectors
from clustering import cluster_books
from taste_analyzer import analyze_taste

load_dotenv()

LIBRARY_API_KEY = os.getenv(
    "LIBRARY_API_KEY",
    "8c5eda89785e6154640860e738f82026d6bfb0c44c8d0f9391ab958fb1c1434d",
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def print_all_keywords(books: list[BookInfo]):
    for i, book in enumerate(books, 1):
        print(f"\n{'━' * 60}")
        print(f"  [{i}] {book.title}")
        print(f"  저자: {book.authors}")
        print(f"  분류: {book.class_nm} ({book.class_no})")
        print(f"  키워드 {len(book.keywords)}개:")
        print(f"{'─' * 60}")
        for j, kw in enumerate(book.keywords, 1):
            end = "\n" if j % 5 == 0 else ""
            print(f"  {kw.word}({kw.weight:.0f})", end=end)
            if j % 5 != 0:
                print(end="\t")
        if len(book.keywords) % 5 != 0:
            print()
    print(f"\n{'━' * 60}")


async def analyze_reading_taste(
    isbn_list: list[str] | None = None,
    random_mode: bool = False,
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    # STEP 1: 데이터 수집
    t0 = time.time()
    if random_mode:
        print("[STEP 1] 정보나루에서 랜덤 10권 수집 중...")
        books = await fetch_random_books(LIBRARY_API_KEY, count=10)
    else:
        print(f"[STEP 1] {len(isbn_list)}권의 키워드 병렬 수집 중...")
        books = await fetch_books_parallel(LIBRARY_API_KEY, isbn_list)

    books = [b for b in books if b.keywords and b.title]
    print(f"  → {len(books)}권 수집 완료 ({time.time() - t0:.1f}s)")

    if not books:
        return "키워드를 가져올 수 있는 책이 없습니다."

    print_all_keywords(books)

    # STEP 2: 키워드 임베딩
    print(f"\n[STEP 2] 키워드 임베딩 생성 중...")
    t1 = time.time()
    book_vectors = await build_all_book_vectors(openai_client, books)
    print(f"  → {len(book_vectors)}권 벡터 생성 완료 ({time.time() - t1:.1f}s)")

    if not book_vectors:
        return "벡터를 생성할 수 있는 책이 없습니다."

    # STEP 3: 클러스터링
    print(f"\n[STEP 3] 클러스터링 (취향 분리)...")
    t2 = time.time()
    clusters = cluster_books(book_vectors)
    print(f"  → {len(clusters)}개 취향 그룹 발견 ({time.time() - t2:.1f}s)")

    for i, c in enumerate(clusters):
        titles = ", ".join(b.title for b in c.books)
        kw_preview = ", ".join(w for w, _ in c.top_keywords[:5])
        kdc_preview = ", ".join(f"{n}({cnt})" for n, cnt in c.kdc_distribution.items())
        print(f"  그룹 {i + 1}: [{titles}]")
        print(f"    키워드: {kw_preview}")
        print(f"    분류: {kdc_preview}")

    # STEP 4: LLM 취향 분석
    print(f"\n[STEP 4] LLM 취향 분석 중...")
    t3 = time.time()
    result = await analyze_taste(openai_client, clusters)
    print(f"  → 분석 완료 ({time.time() - t3:.1f}s)")

    return result


async def main():
    random_mode = "--random" in sys.argv or len(sys.argv) == 1

    isbn_list = None
    if not random_mode:
        isbn_list = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    print("=" * 60)
    print("  독서 취향 분석기")
    print("=" * 60)
    if random_mode:
        print("모드: 랜덤 10권 자동 선택\n")
    else:
        print(f"분석 대상: {len(isbn_list)}권\n")

    result = await analyze_reading_taste(isbn_list=isbn_list, random_mode=random_mode)

    print("\n" + "=" * 60)
    print("  분석 결과")
    print("=" * 60)
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
