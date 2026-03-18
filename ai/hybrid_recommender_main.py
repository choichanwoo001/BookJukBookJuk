"""북적북적 하이브리드 추천 엔진 CLI 진입점

사용 예시:
    # ISBN 기반 추천 (독서 이력 직접 입력)
    python hybrid_recommender_main.py --user-isbn 9788937460470 9788936434120

    # 저장된 프로파일로 추천
    python hybrid_recommender_main.py --load-dir ./saved_pipeline

    # 대화형 모드
    python hybrid_recommender_main.py --interactive

    # 책 카탈로그 구축 후 추천
    python hybrid_recommender_main.py \\
        --catalog-isbn 9788937460470 9788936434120 9788954672597 \\
        --user-isbn 9788937460470 \\
        --top-k 5 --save-dir ./saved_pipeline
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hybrid_recommender import HybridRecommenderPipeline, UserProfile
from hybrid_recommender.phase3_scoring.user_profile import ActionType, UserAction

load_dotenv()


# ── 기본 예시 데이터 ──────────────────────────────────────────────────────────

SAMPLE_CATALOG = [
    "9788937460470",  # 채식주의자 (한강)
    "9788936434120",  # 소년이 온다 (한강)
    "9788954672597",  # 흰 (한강)
    "9788934972464",  # 82년생 김지영 (조남주)
    "9788937462788",  # 아몬드 (손원평)
]

SAMPLE_USER_HISTORY = [
    "9788937460470",  # 채식주의자
    "9788934972464",  # 82년생 김지영
]


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


async def run_recommend(args: argparse.Namespace) -> None:
    """추천 파이프라인을 실행한다."""
    _print_header()

    # 파이프라인 초기화
    pipeline = HybridRecommenderPipeline.from_env(
        user_id=args.user_id,
        noise_threshold=args.noise_threshold,
        mmr_lambda=args.mmr_lambda,
        epsilon=args.epsilon,
    )

    # 저장된 상태 로드
    if args.load_dir and os.path.exists(args.load_dir):
        print(f"[로드] {args.load_dir}")
        pipeline.load(args.load_dir)
    else:
        # 카탈로그 구축
        catalog_isbns = args.catalog_isbn or SAMPLE_CATALOG
        print(f"[카탈로그] {len(catalog_isbns)}권 등록 시작...")
        await pipeline.add_books(
            isbn_list=catalog_isbns,
            concurrency=args.concurrency,
        )

    # 사용자 이력 추가
    user_isbns = args.user_isbn or SAMPLE_USER_HISTORY
    print(f"\n[사용자 이력] {len(user_isbns)}권 등록 중...")
    for isbn in user_isbns:
        title = pipeline._book_titles.get(isbn, isbn)
        pipeline.user_profile.add_read(isbn, title)
        print(f"  - {title} ({isbn})")
    print(f"\n  {pipeline.user_profile.summary()}")

    # 추천 실행
    print(f"\n[추천] top_k={args.top_k} 실행 중...")
    results = await pipeline.recommend(
        top_k=args.top_k,
        with_explanation=not args.no_explanation,
    )

    _print_results(results)

    # 파이프라인 저장
    if args.save_dir:
        pipeline.save(args.save_dir)

    # 상태 출력
    status = pipeline.status()
    print(f"파이프라인 상태: {status}")


async def run_interactive(args: argparse.Namespace) -> None:
    """대화형 모드로 실행한다."""
    _print_header()
    print("대화형 모드 시작. 'help' 로 명령어 확인, 'quit' 로 종료.\n")

    pipeline = HybridRecommenderPipeline.from_env(user_id=args.user_id)

    if args.load_dir and os.path.exists(args.load_dir):
        pipeline.load(args.load_dir)

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

    # 모드 선택
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="대화형 모드 실행",
    )

    # 데이터 입력
    parser.add_argument(
        "--user-isbn", nargs="+",
        metavar="ISBN",
        help="사용자 독서 이력 ISBN 목록",
    )
    parser.add_argument(
        "--catalog-isbn", nargs="+",
        metavar="ISBN",
        help="카탈로그 구축용 ISBN 목록 (없으면 샘플 사용)",
    )

    # 추천 설정
    parser.add_argument("--top-k", type=int, default=5, help="추천 수 (기본 5)")
    parser.add_argument("--user-id", default="default_user", help="사용자 ID")
    parser.add_argument(
        "--no-explanation",
        action="store_true",
        help="LLM 설명 생성 비활성화 (빠른 실행)",
    )

    # 파이프라인 파라미터
    parser.add_argument("--noise-threshold", type=float, default=0.50,
                        help="KG 노이즈 필터 임계값 (기본 0.50)")
    parser.add_argument("--mmr-lambda", type=float, default=0.6,
                        help="MMR 관련성-다양성 균형 (기본 0.6)")
    parser.add_argument("--epsilon", type=float, default=0.15,
                        help="Epsilon-greedy 탐색률 (기본 0.15)")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="병렬 API 호출 수 (기본 3)")

    # 저장/로드
    parser.add_argument("--save-dir", help="파이프라인 저장 경로")
    parser.add_argument("--load-dir", help="파이프라인 로드 경로")

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(run_interactive(args))
    else:
        asyncio.run(run_recommend(args))


if __name__ == "__main__":
    main()
