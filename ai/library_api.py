import asyncio
import random
from dataclasses import dataclass

import httpx

BASE_URL = "http://data4library.kr/api"

KDC_CATEGORIES = [
    ("0", "총류"),
    ("1", "철학"),
    ("2", "종교"),
    ("3", "사회과학"),
    ("4", "자연과학"),
    ("5", "기술과학"),
    ("6", "예술"),
    ("7", "언어"),
    ("8", "문학"),
    ("9", "역사"),
]


@dataclass
class BookKeyword:
    word: str
    weight: float


@dataclass
class BookInfo:
    isbn13: str
    title: str
    authors: str
    publisher: str
    class_no: str
    class_nm: str
    keywords: list[BookKeyword]


async def fetch_keywords(
    client: httpx.AsyncClient,
    auth_key: str,
    isbn13: str,
) -> list[BookKeyword]:
    resp = await client.get(
        f"{BASE_URL}/keywordList",
        params={
            "authKey": auth_key,
            "isbn13": isbn13,
            "additionalYN": "N",
            "format": "json",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    keywords: list[BookKeyword] = []
    items = data.get("response", {}).get("items", [])
    if isinstance(items, list):
        for item in items:
            entry = item.get("item", item)
            keywords.append(
                BookKeyword(
                    word=entry["word"],
                    weight=float(entry["weight"]),
                )
            )
    return keywords


async def fetch_book_detail(
    client: httpx.AsyncClient,
    auth_key: str,
    isbn13: str,
) -> dict:
    resp = await client.get(
        f"{BASE_URL}/srchDtlList",
        params={
            "authKey": auth_key,
            "isbn13": isbn13,
            "format": "json",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    detail = data.get("response", {}).get("detail", [])
    if detail:
        book = detail[0].get("book", {})
        return {
            "title": book.get("bookname", ""),
            "authors": book.get("authors", ""),
            "publisher": book.get("publisher", ""),
            "class_no": book.get("class_no", ""),
            "class_nm": book.get("class_nm", ""),
        }
    return {
        "title": "",
        "authors": "",
        "publisher": "",
        "class_no": "",
        "class_nm": "",
    }


async def _fetch_single_book(
    client: httpx.AsyncClient,
    auth_key: str,
    isbn13: str,
) -> BookInfo:
    keywords, detail = await asyncio.gather(
        fetch_keywords(client, auth_key, isbn13),
        fetch_book_detail(client, auth_key, isbn13),
    )
    return BookInfo(
        isbn13=isbn13,
        title=detail["title"],
        authors=detail["authors"],
        publisher=detail["publisher"],
        class_no=detail["class_no"],
        class_nm=detail["class_nm"],
        keywords=keywords,
    )


async def fetch_books_parallel(
    auth_key: str,
    isbn_list: list[str],
) -> list[BookInfo]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            _fetch_single_book(client, auth_key, isbn)
            for isbn in isbn_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    books: list[BookInfo] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"[WARN] ISBN {isbn_list[i]} 조회 실패: {result}")
            continue
        books.append(result)
    return books


async def _fetch_popular_by_kdc(
    client: httpx.AsyncClient,
    auth_key: str,
    kdc: str,
    page_size: int = 200,
) -> list[str]:
    resp = await client.get(
        f"{BASE_URL}/loanItemSrch",
        params={
            "authKey": auth_key,
            "kdc": kdc,
            "pageSize": str(page_size),
            "format": "json",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    isbns: list[str] = []
    docs = data.get("response", {}).get("docs", [])
    for doc in docs:
        entry = doc.get("doc", doc)
        isbn = entry.get("isbn13", "")
        if isbn:
            isbns.append(isbn)
    return isbns


async def fetch_random_books(
    auth_key: str,
    count: int = 10,
) -> list[BookInfo]:
    selected_kdcs = random.sample(KDC_CATEGORIES, k=min(count, len(KDC_CATEGORIES)))

    async with httpx.AsyncClient(timeout=30.0) as client:
        kdc_tasks = [
            _fetch_popular_by_kdc(client, auth_key, kdc, page_size=200)
            for kdc, _ in selected_kdcs
        ]
        kdc_results = await asyncio.gather(*kdc_tasks, return_exceptions=True)

    isbn_pool: list[tuple[str, str]] = []
    for i, result in enumerate(kdc_results):
        if isinstance(result, Exception):
            print(f"[WARN] KDC {selected_kdcs[i][1]} 조회 실패: {result}")
            continue
        kdc_name = selected_kdcs[i][1]
        for isbn in result:
            isbn_pool.append((isbn, kdc_name))

    if not isbn_pool:
        return []

    random.shuffle(isbn_pool)

    picked_isbns: list[str] = []
    seen: set[str] = set()
    for isbn, _ in isbn_pool:
        if isbn not in seen:
            seen.add(isbn)
            picked_isbns.append(isbn)
        if len(picked_isbns) >= count * 2:
            break

    print(f"  후보 ISBN {len(picked_isbns)}개 중 키워드 있는 10권 선별 중...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            _fetch_single_book(client, auth_key, isbn)
            for isbn in picked_isbns
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    books: list[BookInfo] = []
    for result in results:
        if isinstance(result, Exception):
            continue
        if result.keywords and result.title:
            books.append(result)
        if len(books) >= count:
            break

    return books
