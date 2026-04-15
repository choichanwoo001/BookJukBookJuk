"""북적북적 하이브리드 추천 엔진 CLI 진입점

카탈로그·독서 이력은 로컬 SQLite 없이 CLI·저장된 파이프라인만 사용합니다.

E2E 권장 순서 (KG·임베딩·사용자 DB 기반 추천):
  1) `backend/scripts/seed_hybrid_recommender_e2e.py` 등으로 `books`/`book_api_cache` 시드
  2) `HYBRID_USE_SUPABASE=1`, `HYBRID_PERSIST_KG=1` 로 `--catalog-isbn` 으로 `add_books` →
     `kg_nodes`/`kg_edges` + `book_vectors` 생성·저장
  3) Supabase 에 `ratings` / `shelves`+`shelf_books` / `book_user_states` 등 사용자 행 삽입
  4) `--supabase-user-id <users.Key>` 로 프로파일 로드 후 추천 (또는 `--skip-catalog` 로
     이미 DB 에 쌓인 KG·벡터만 로드)

ISBN 등록 시 Supabase 에서 메타를 읽으려면 `.env` 에 `HYBRID_USE_SUPABASE=1`,
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`(또는 ANON) 를 두거나 `--use-supabase` 를 사용합니다.
`book_api_cache` 는 RLS 때문에 서비스 롤 권장.

KG 를 DB 에 저장·로드하려면 `HYBRID_PERSIST_KG=1`(또는 `--persist-kg`) 과 서비스 롤 키로
`kg_nodes`/`kg_edges` 마이그레이션(`20260414120000_hybrid_kg_tables.sql`) 이 적용되어 있어야 합니다.

임베딩은 `book_vectors` 테이블에 upsert 됩니다. 기본은 KG 와 동일하게 켜지며,
끄려면 `HYBRID_PERSIST_EMBEDDINGS=0` 또는 `--no-persist-embeddings` 를 사용합니다.

사용 예시:
    # ISBN으로 카탈로그 + 사용자 이력 지정
    python hybrid_recommender_main.py --catalog-isbn 9788937460470 9788936434120 \\
        --user-isbn 9788937460470

    # Supabase 사용자 키로 이력 로드 (ratings / shelves / book_user_states)
    python hybrid_recommender_main.py --catalog-isbn 9788937460470 \\
        --supabase-user-id my_user_key --use-supabase --persist-kg

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
from hybrid_recommender.supabase_book_context import create_supabase_client_from_env
from hybrid_recommender.supabase_user_profile import load_user_profile_from_supabase


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
    print(f"  추천 도서 TOP {len(results)}")
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
            print(f"   설명: {r.explanation}")
        if r.kg_paths:
            for path in r.kg_paths[:1]:
                path_str = " → ".join(
                    f"{head}→{tail}" for head, rel, tail in path
                )
                print(f"   KG: {path_str}")

    print(f"\n{'─' * 60}\n")


def _exit(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _apply_supabase_user_profile(pipeline: HybridRecommenderPipeline, supabase_user_id: str) -> None:
    """`ratings` / `shelves` / `book_user_states` 를 읽어 `pipeline.user_profile` 을 덮어쓴다."""
    sb = pipeline.supabase_client or create_supabase_client_from_env()
    if not sb:
        _exit("[오류] --supabase-user-id 는 SUPABASE_URL 과 SUPABASE_SERVICE_ROLE_KEY(또는 ANON) 가 필요합니다.")
    pipeline.user_profile = load_user_profile_from_supabase(sb, supabase_user_id)
    print(f"\n[사용자 이력] Supabase 사용자 {supabase_user_id} 로드")
    print(f"  {pipeline.user_profile.summary()}")


async def run_recommend(args: argparse.Namespace) -> None:
    """추천 파이프라인을 실행한다."""
    _print_header()

    if getattr(args, "supabase_user_id", None):
        args.user_id = args.supabase_user_id

    supabase_kw: dict = {}
    if getattr(args, "use_supabase", False):
        supabase_kw["use_supabase"] = True
    elif getattr(args, "no_supabase", False):
        supabase_kw["use_supabase"] = False
    if args.persist_kg and args.no_persist_kg:
        _exit("[오류] --persist-kg 와 --no-persist-kg 는 함께 쓸 수 없습니다.")
    if args.persist_kg:
        supabase_kw["persist_kg"] = True
    elif args.no_persist_kg:
        supabase_kw["persist_kg"] = False
    if args.persist_embeddings and args.no_persist_embeddings:
        _exit("[오류] --persist-embeddings 와 --no-persist-embeddings 는 함께 쓸 수 없습니다.")
    if args.persist_embeddings:
        supabase_kw["persist_embeddings"] = True
    elif args.no_persist_embeddings:
        supabase_kw["persist_embeddings"] = False

    if getattr(args, "skip_catalog", False) and args.catalog_isbn:
        _exit("[오류] --skip-catalog 와 --catalog-isbn 은 함께 쓸 수 없습니다.")

    if args.load_dir:
        if not os.path.exists(args.load_dir):
            _exit(f"[오류] --load-dir 경로가 없습니다: {args.load_dir}")
        print(f"[로드] {args.load_dir}")
        pipeline = HybridRecommenderPipeline.from_env(
            user_id=args.user_id,
            noise_threshold=args.noise_threshold,
            mmr_lambda=args.mmr_lambda,
            epsilon=args.epsilon,
            **supabase_kw,
        )
        pipeline.load(args.load_dir)
    elif getattr(args, "skip_catalog", False):
        pipeline = HybridRecommenderPipeline.from_env(
            user_id=args.user_id,
            noise_threshold=args.noise_threshold,
            mmr_lambda=args.mmr_lambda,
            epsilon=args.epsilon,
            **supabase_kw,
        )
        print("[카탈로그] --skip-catalog: add_books 생략 (Supabase 등에 이미 KG/벡터가 있어야 합니다).")
    elif args.catalog_isbn:
        pipeline = HybridRecommenderPipeline.from_env(
            user_id=args.user_id,
            noise_threshold=args.noise_threshold,
            mmr_lambda=args.mmr_lambda,
            epsilon=args.epsilon,
            **supabase_kw,
        )

        print(f"[카탈로그] {len(args.catalog_isbn)}권 등록 시작...")
        await pipeline.add_books(
            isbn_list=args.catalog_isbn,
            concurrency=args.concurrency,
        )
    else:
        _exit(
            "[오류] `--load-dir`, `--catalog-isbn`, `--skip-catalog` 중 하나를 지정하세요."
        )

    loaded_from_dir = bool(args.load_dir and os.path.exists(args.load_dir))

    if args.supabase_user_id:
        _apply_supabase_user_profile(pipeline, args.supabase_user_id)

    if args.user_isbn:
        print(f"\n[사용자 이력] CLI에서 {len(args.user_isbn)}권 추가...")
        for isbn in args.user_isbn:
            title = pipeline._book_titles.get(isbn, isbn)
            pipeline.user_profile.add_read(isbn, title)
            print(f"  - {title} ({isbn})")

    if not loaded_from_dir and not args.supabase_user_id and not args.user_isbn:
        _exit("[오류] `--user-isbn` 또는 `--supabase-user-id` 로 독서 이력을 지정하세요.")

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

    if getattr(args, "supabase_user_id", None):
        args.user_id = args.supabase_user_id

    supabase_kw: dict = {}
    if getattr(args, "use_supabase", False):
        supabase_kw["use_supabase"] = True
    elif getattr(args, "no_supabase", False):
        supabase_kw["use_supabase"] = False
    if args.persist_kg and args.no_persist_kg:
        _exit("[오류] --persist-kg 와 --no-persist-kg 는 함께 쓸 수 없습니다.")
    if args.persist_kg:
        supabase_kw["persist_kg"] = True
    elif args.no_persist_kg:
        supabase_kw["persist_kg"] = False
    if args.persist_embeddings and args.no_persist_embeddings:
        _exit("[오류] --persist-embeddings 와 --no-persist-embeddings 는 함께 쓸 수 없습니다.")
    if args.persist_embeddings:
        supabase_kw["persist_embeddings"] = True
    elif args.no_persist_embeddings:
        supabase_kw["persist_embeddings"] = False

    pipeline = HybridRecommenderPipeline.from_env(
        user_id=args.user_id,
        noise_threshold=args.noise_threshold,
        mmr_lambda=args.mmr_lambda,
        epsilon=args.epsilon,
        **supabase_kw,
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

    if args.supabase_user_id:
        _apply_supabase_user_profile(pipeline, args.supabase_user_id)

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
        help="배치 모드에서 사용자 독서 이력(ISBN). --supabase-user-id 없을 때 --load-dir 없으면 필수",
    )
    parser.add_argument(
        "--supabase-user-id",
        metavar="USER_KEY",
        default=None,
        help="public.users.Key 와 동일한 ID. ratings / shelves / book_user_states 에서 이력 로드",
    )
    parser.add_argument(
        "--catalog-isbn", nargs="+",
        metavar="ISBN",
        help="카탈로그 구축용 ISBN. --load-dir·--skip-catalog 없을 때 필요",
    )
    parser.add_argument(
        "--skip-catalog",
        action="store_true",
        help="add_books 생략. HYBRID_PERSIST_KG 등으로 이미 DB에 KG·book_vectors가 있을 때",
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

    sb = parser.add_mutually_exclusive_group()
    sb.add_argument(
        "--use-supabase",
        action="store_true",
        help="ISBN 등록 시 Supabase public.books(+book_api_cache) 우선 (SUPABASE_URL/KEY 필요)",
    )
    sb.add_argument(
        "--no-supabase",
        action="store_true",
        help="환경에 HYBRID_USE_SUPABASE 가 있어도 API 수집만 사용",
    )
    parser.add_argument(
        "--persist-kg",
        action="store_true",
        help="KG를 Supabase에 저장/시작 시 로드 (HYBRID_PERSIST_KG=1 과 동일)",
    )
    parser.add_argument(
        "--no-persist-kg",
        action="store_true",
        help="HYBRID_PERSIST_KG 가 있어도 KG DB 영속 비활성화",
    )
    parser.add_argument(
        "--persist-embeddings",
        action="store_true",
        help="임베딩을 book_vectors 에 저장 (HYBRID_PERSIST_EMBEDDINGS=1)",
    )
    parser.add_argument(
        "--no-persist-embeddings",
        action="store_true",
        help="HYBRID_PERSIST_EMBEDDINGS 가 있어도 임베딩 DB 동기화 비활성화",
    )

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(run_interactive(args))
    else:
        asyncio.run(run_recommend(args))


if __name__ == "__main__":
    main()
