"""북적북적 하이브리드 추천 엔진 CLI 진입점

사용 예시:
    # books.db 카탈로그 + DB 독서 이력(기본 user dev_user_1)
    python hybrid_recommender_main.py --user-id dev_user_1

    # ISBN 직접 지정 (독서 이력은 DB 대신 CLI)
    python hybrid_recommender_main.py --catalog-isbn 9788937460470 9788936434120 \\
        --user-isbn 9788937460470

    # 저장된 프로파일로 추천
    python hybrid_recommender_main.py --load-dir ./saved_pipeline

    # 대화형 모드
    python hybrid_recommender_main.py --interactive

    # DB에서 BookContext 우선 (API 호출 최소화)
    python hybrid_recommender_main.py --prefer-db-book-context
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from book_seeder.db import DEV_TEST_USER_ID, create_schema, seed_test_user_reads
from hybrid_recommender import HybridRecommenderPipeline
from hybrid_recommender.sqlite_catalog import (
    list_catalog_isbns,
    load_user_read_actions,
    resolve_books_db_path,
)

load_dotenv()


def _print_header() -> None:
    print("=" * 60)
    print("  북적북적 하이브리드 추천 엔진")
    print("  Knowledge Graph + RippleNet + MMR + XAI")
    print("=" * 60)
    print()


def _print_results(results: list) -> None:
    if not results:
        print("추천 결과가 없습니다.")
        return

    print(f"\n{'─' * 60}")
    print(f"  📚 추천 도서 TOP {len(results)}")
    print(f"{'─' * 60}")

    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r.title}")
        if r.authors:
            print(f"   저자: {r.authors}")
        if r.publisher:
            print(f"   출판사: {r.publisher} ({r.published_year})")
        if r.kdc_class:
            print(f"   분류: {r.kdc_class}")
        print(
            f"   점수: {r.final_score:.3f} "
            f"[그래프={r.graph_score:.3f} | 벡터={r.vector_score:.3f} | α={r.alpha_used:.2f}]"
        )
        if r.explanation:
            print(f"   💡 {r.explanation}")
        if r.kg_paths:
            for path in r.kg_paths[:1]:
                path_str = " → ".join(
                    f"{head}→{tail}" for head, rel, tail in path
                )
                print(f"   🔗 KG: {path_str}")

    print(f"\n{'─' * 60}\n")


def _exit(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


async def run_recommend(args: argparse.Namespace) -> None:
    """추천 파이프라인을 실행한다."""
    _print_header()

    if args.load_dir:
        if not os.path.exists(args.load_dir):
            _exit(f"[오류] --load-dir 경로가 없습니다: {args.load_dir}")
        print(f"[로드] {args.load_dir}")
        pipeline = HybridRecommenderPipeline.from_env(
            user_id=args.user_id,
            noise_threshold=args.noise_threshold,
            mmr_lambda=args.mmr_lambda,
            epsilon=args.epsilon,
        )
        pipeline.load(args.load_dir)
    else:
        db_path = resolve_books_db_path(args.db_path)
        create_schema(db_path)

        if not args.no_dev_seed:
            n = seed_test_user_reads(db_path, user_id=args.user_id)
            if n > 0:
                print(f"[시드] 사용자 {args.user_id!r} 독서 이력 {n}건 추가")

        catalog_isbns = args.catalog_isbn
        if not catalog_isbns:
            catalog_isbns = list_catalog_isbns(
                db_path,
                sector=args.catalog_sector,
                limit=args.catalog_limit,
            )
        if not catalog_isbns:
            _exit(
                "[오류] 카탈로그 ISBN이 없습니다. "
                "`--catalog-isbn`을 주거나 books.db에 books 행이 있어야 합니다."
            )

        pipeline = HybridRecommenderPipeline.from_env(
            user_id=args.user_id,
            noise_threshold=args.noise_threshold,
            mmr_lambda=args.mmr_lambda,
            epsilon=args.epsilon,
            books_db_path=db_path,
            prefer_db_book_context=args.prefer_db_book_context,
        )

        print(f"[카탈로그] {len(catalog_isbns)}권 등록 시작...")
        await pipeline.add_books(
            isbn_list=catalog_isbns,
            concurrency=args.concurrency,
        )

    loaded_from_dir = bool(args.load_dir and os.path.exists(args.load_dir))
    if not loaded_from_dir:
        if args.user_isbn:
            print(f"\n[사용자 이력] CLI에서 {len(args.user_isbn)}권 등록 중...")
            for isbn in args.user_isbn:
                title = pipeline._book_titles.get(isbn, isbn)
                pipeline.user_profile.add_read(isbn, title)
                print(f"  - {title} ({isbn})")
        else:
            db_path = resolve_books_db_path(args.db_path)
            records = load_user_read_actions(args.user_id, db_path)
            if not records:
                _exit(
                    "[오류] DB에 독서 이력이 없습니다. "
                    "`--user-isbn`으로 넘기거나, 시드(`--no-dev-seed` 해제) 및 `--user-id`를 확인하세요."
                )
            print(f"\n[사용자 이력] DB에서 {len(records)}권 로드...")
            for rec in records:
                pipeline.user_profile.add_read(
                    rec.isbn13,
                    rec.title,
                    timestamp=rec.occurred_at,
                    rating=rec.rating,
                )
                print(f"  - {rec.title} ({rec.isbn13})")

    print(f"\n  {pipeline.user_profile.summary()}")

    print(f"\n[추천] top_k={args.top_k} 실행 중...")
    results = await pipeline.recommend(
        top_k=args.top_k,
        with_explanation=not args.no_explanation,
    )

    _print_results(results)

    if args.save_dir:
        pipeline.save(args.save_dir)

    status = pipeline.status()
    print(f"파이프라인 상태: {status}")


async def run_interactive(args: argparse.Namespace) -> None:
    """대화형 모드로 실행한다."""
    _print_header()
    print("대화형 모드 시작. 'help' 로 명령어 확인, 'quit' 로 종료.\n")

    db_path = resolve_books_db_path(args.db_path)
    create_schema(db_path)

    pipeline = HybridRecommenderPipeline.from_env(
        user_id=args.user_id,
        books_db_path=db_path,
        prefer_db_book_context=args.prefer_db_book_context,
    )

    if args.load_dir and os.path.exists(args.load_dir):
        pipeline.load(args.load_dir)
    elif args.interactive_load_catalog:
        if not args.no_dev_seed:
            seed_test_user_reads(db_path, user_id=args.user_id)
        isbns = args.catalog_isbn or list_catalog_isbns(
            db_path,
            sector=args.catalog_sector,
            limit=args.catalog_limit,
        )
        if isbns:
            print(f"[카탈로그] DB에서 {len(isbns)}권 로드...")
            await pipeline.add_books(isbn_list=isbns, concurrency=args.concurrency)
        else:
            print("[WARN] DB에 books가 없어 카탈로그를 건너뜁니다. add <isbn> 으로 등록하세요.")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("quit", "exit", "종료"):
            print("종료합니다.")
            break

        elif cmd == "help":
            print("""
명령어:
  add <isbn>          책을 ISBN 으로 등록
  read <isbn>         독서 이력 추가 (완독)
  recommend [n]       추천 실행 (기본 5권)
  status              현재 상태 확인
  save <path>         상태 저장
  load <path>         상태 로드
  quit                종료
""")

        elif cmd.startswith("add "):
            isbn = cmd[4:].strip()
            try:
                await pipeline.add_book(isbn=isbn)
            except Exception as e:
                print(f"오류: {e}")

        elif cmd.startswith("read "):
            isbn = cmd[5:].strip()
            title = pipeline._book_titles.get(isbn, isbn)
            pipeline.user_profile.add_read(isbn, title)
            print(f"독서 이력 추가: {title}")

        elif cmd.startswith("recommend"):
            parts = cmd.split()
            n = int(parts[1]) if len(parts) > 1 else 5
            try:
                results = await pipeline.recommend(top_k=n)
                _print_results(results)
            except Exception as e:
                print(f"추천 오류: {e}")

        elif cmd == "status":
            print(pipeline.status())

        elif cmd.startswith("save "):
            path = cmd[5:].strip()
            pipeline.save(path)

        elif cmd.startswith("load "):
            path = cmd[5:].strip()
            pipeline.load(path)

        else:
            print(f"알 수 없는 명령어: '{user_input}'. 'help' 로 확인하세요.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="북적북적 하이브리드 추천 엔진",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="대화형 모드 실행",
    )
    parser.add_argument(
        "--interactive-load-catalog",
        action="store_true",
        help="대화형 시작 시 DB에서 카탈로그 ISBN을 불러와 add_books",
    )

    parser.add_argument(
        "--user-isbn", nargs="+",
        metavar="ISBN",
        help="사용자 독서 이력(지정 시 DB 이력 대신 사용)",
    )
    parser.add_argument(
        "--catalog-isbn", nargs="+",
        metavar="ISBN",
        help="카탈로그 구축용 ISBN(미지정 시 books.db에서 로드, 기본은 전체 권수)",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="books.db 경로(기본: BOOKS_DB_PATH 환경변수 또는 ai/data/books.db)",
    )
    parser.add_argument(
        "--catalog-sector",
        type=int,
        default=None,
        help="카탈로그를 KDC sector로 필터(미지정이면 전체)",
    )
    parser.add_argument(
        "--catalog-limit",
        type=int,
        default=0,
        help="DB에서 가져올 최대 권수(기본 0=제한 없음·전체, 양수면 상한)",
    )
    parser.add_argument(
        "--no-dev-seed",
        action="store_true",
        help="dev_user_1 스타일 시드(seed_test_user_reads) 생략",
    )
    parser.add_argument(
        "--prefer-db-book-context",
        action="store_true",
        help="books.db에 있으면 BookContext를 DB에서 조립(API 호출 생략)",
    )

    parser.add_argument("--top-k", type=int, default=5, help="추천 수 (기본 5)")
    parser.add_argument(
        "--user-id",
        default=DEV_TEST_USER_ID,
        help=f"사용자 ID (기본 {DEV_TEST_USER_ID})",
    )
    parser.add_argument(
        "--no-explanation",
        action="store_true",
        help="LLM 설명 생성 비활성화 (빠른 실행)",
    )

    parser.add_argument("--noise-threshold", type=float, default=0.50,
                        help="KG 노이즈 필터 임계값 (기본 0.50)")
    parser.add_argument("--mmr-lambda", type=float, default=0.6,
                        help="MMR 관련성-다양성 균형 (기본 0.6)")
    parser.add_argument("--epsilon", type=float, default=0.15,
                        help="Epsilon-greedy 탐색률 (기본 0.15)")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="병렬 API 호출 수 (기본 3)")

    parser.add_argument("--save-dir", help="파이프라인 저장 경로")
    parser.add_argument("--load-dir", help="파이프라인 로드 경로")

    args = parser.parse_args()

    if args.catalog_limit is not None and args.catalog_limit <= 0:
        args.catalog_limit = None

    if args.interactive:
        asyncio.run(run_interactive(args))
    else:
        asyncio.run(run_recommend(args))


if __name__ == "__main__":
    main()
