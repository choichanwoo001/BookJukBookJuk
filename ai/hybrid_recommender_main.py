"""북적북적 하이브리드 추천 엔진 CLI 진입점

카탈로그·독서 이력은 로컬 SQLite 없이 CLI·저장된 파이프라인만 사용합니다.

사용 예시:
    # ISBN으로 카탈로그 + 사용자 이력 지정
    python hybrid_recommender_main.py --catalog-isbn 9788937460470 9788936434120 \\
        --user-isbn 9788937460470

    # 저장된 프로파일로 추천
    python hybrid_recommender_main.py --load-dir ./saved_pipeline

    # 대화형 모드
    python hybrid_recommender_main.py --interactive
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_AI_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _AI_DIR.parent
_env = _REPO_ROOT / ".env"
if _env.is_file():
    load_dotenv(_env)

sys.path.insert(0, str(_AI_DIR))

DEV_TEST_USER_ID = "dev_user_1"

from hybrid_recommender import HybridRecommenderPipeline


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
        if not args.catalog_isbn:
            _exit(
                "[오류] `--catalog-isbn`으로 ISBN 목록을 지정하세요. "
                "(카탈로그는 Supabase·앱에서 관리하며 로컬 DB는 사용하지 않습니다.)"
            )

        pipeline = HybridRecommenderPipeline.from_env(
            user_id=args.user_id,
            noise_threshold=args.noise_threshold,
            mmr_lambda=args.mmr_lambda,
            epsilon=args.epsilon,
        )

        print(f"[카탈로그] {len(args.catalog_isbn)}권 등록 시작...")
        await pipeline.add_books(
            isbn_list=args.catalog_isbn,
            concurrency=args.concurrency,
        )

    loaded_from_dir = bool(args.load_dir and os.path.exists(args.load_dir))
    if not loaded_from_dir:
        if not args.user_isbn:
            _exit(
                "[오류] `--user-isbn`으로 독서 이력(ISBN)을 지정하세요."
            )
        print(f"\n[사용자 이력] CLI에서 {len(args.user_isbn)}권 등록 중...")
        for isbn in args.user_isbn:
            title = pipeline._book_titles.get(isbn, isbn)
            pipeline.user_profile.add_read(isbn, title)
            print(f"  - {title} ({isbn})")

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

    pipeline = HybridRecommenderPipeline.from_env(
        user_id=args.user_id,
        noise_threshold=args.noise_threshold,
        mmr_lambda=args.mmr_lambda,
        epsilon=args.epsilon,
    )

    if args.load_dir and os.path.exists(args.load_dir):
        pipeline.load(args.load_dir)
    elif args.interactive_load_catalog and args.catalog_isbn:
        print(f"[카탈로그] --catalog-isbn {len(args.catalog_isbn)}권 등록...")
        await pipeline.add_books(
            isbn_list=args.catalog_isbn,
            concurrency=args.concurrency,
        )
    elif args.interactive_load_catalog:
        print(
            "[안내] `--interactive-load-catalog` 는 `--catalog-isbn` 과 함께 쓰거나, "
            "시작 후 `add <isbn>` 으로 등록하세요."
        )

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
        help="대화형 시작 시 --catalog-isbn 목록으로 add_books",
    )

    parser.add_argument(
        "--user-isbn", nargs="+",
        metavar="ISBN",
        help="배치 모드에서 사용자 독서 이력(ISBN). --load-dir 없을 때 필수",
    )
    parser.add_argument(
        "--catalog-isbn", nargs="+",
        metavar="ISBN",
        help="카탈로그 구축용 ISBN. --load-dir 없을 때 필수",
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

    if args.interactive:
        asyncio.run(run_interactive(args))
    else:
        asyncio.run(run_recommend(args))


if __name__ == "__main__":
    main()
