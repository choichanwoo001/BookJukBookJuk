#!/usr/bin/env python3
"""북적북적 도서 시더 — SQLite에 1000권 수집

KDC 10개 섹터(0-9) × 100권, 총 1000권을 ai/data/books.db에 저장합니다.
저자 Wikipedia 필수 / 400권은 한국 저자 + 2020년 이후 출판.

사용법:
    python book_seeder_main.py --all            # 모든 섹터 실행
    python book_seeder_main.py --sector 8       # KDC 8(문학)만 실행
    python book_seeder_main.py --reset          # DB 초기화 후 전체 실행
    python book_seeder_main.py --status         # 현재 수집 진행 상황 출력

필요 환경변수 (ai/.env):
    LIBRARY_API_KEY  정보나루 API 키  https://www.data4library.kr/
    ALADIN_API_KEY   알라딘 TTB API 키 (선택, 없으면 설명 등 일부 정보 미수집)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

from book_seeder.db import (
    DB_PATH,
    count_korean_recent,
    create_schema,
    get_sector_stats,
    reset_schema,
)
from book_seeder.orchestrator import (
    KDC_NAMES,
    TARGET_PER_SECTOR,
    TOTAL_KR_TARGET,
    run_all_sectors,
    run_sector,
)


def print_status() -> None:
    stats = get_sector_stats()
    total_kr = count_korean_recent()

    header = f"{'섹터':<5} {'분류명':<10} {'수집':>6} {'한국':>6} {'최근':>6} {'KR최근':>7}"
    print(f"\n{header}")
    print("-" * len(header))

    present = {}
    grand_total = 0
    for row in stats:
        present[row["sector"]] = row
        grand_total += row["total"]

    for s in range(10):
        row = present.get(s)
        if row:
            bar = "#" * (row["total"] * 20 // TARGET_PER_SECTOR)
            print(
                f"  {s:<3} {KDC_NAMES[s]:<10} "
                f"{row['total']:>6} {row['korean']:>6} {row['recent']:>6} {row['korean_recent']:>7}"
                f"  {bar}"
            )
        else:
            print(f"  {s:<3} {KDC_NAMES[s]:<10} {'0':>6} {'0':>6} {'0':>6} {'0':>7}")

    print("-" * len(header))
    print(f"  합계{' '*9} {grand_total:>6}{'':>6}{'':>6} {total_kr:>7}  (목표: {TOTAL_KR_TARGET})")
    print(f"\nDB 경로: {DB_PATH}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="북적북적 도서 시더",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--all", action="store_true", help="10개 섹터 전체 실행")
    parser.add_argument(
        "--sector",
        type=int,
        choices=range(10),
        metavar="N",
        help="특정 KDC 섹터만 실행 (0-9)",
    )
    parser.add_argument("--reset", action="store_true", help="DB 초기화 후 전체 실행")
    parser.add_argument("--status", action="store_true", help="현재 수집 진행 상황 출력")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    library_api_key = os.environ.get("LIBRARY_API_KEY", "")
    aladin_api_key = os.environ.get("ALADIN_API_KEY", "")

    if not library_api_key:
        print("[ERROR] LIBRARY_API_KEY 환경변수가 설정되지 않았습니다.")
        print("       발급: https://www.data4library.kr/")
        sys.exit(1)

    if not aladin_api_key:
        print("[WARN] ALADIN_API_KEY가 없습니다. 책 설명·저자 소개 등이 누락될 수 있습니다.")

    if args.reset:
        print("[RESET] DB 초기화 중...")
        reset_schema()
        print("[RESET] 완료.")

    create_schema()

    if args.sector is not None:
        asyncio.run(
            run_sector(
                sector=args.sector,
                library_api_key=library_api_key,
                aladin_api_key=aladin_api_key,
                kr_target=TOTAL_KR_TARGET // 10,
            )
        )
    elif args.all or args.reset:
        asyncio.run(
            run_all_sectors(
                library_api_key=library_api_key,
                aladin_api_key=aladin_api_key,
            )
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
