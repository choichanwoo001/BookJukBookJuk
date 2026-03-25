"""저자 Wikipedia 존재 여부 경량 확인."""
from __future__ import annotations

import os
import re

import httpx

# data_collector.py 의 저자명 파싱 로직(lines 321-322)을 미러링
_ROLE_PREFIX_RE = re.compile(r"^[^:：]+[:：]\s*")
_TRAILING_ROLE_RE = re.compile(r"\s+(지음|저|글|그림|옮김|편저|엮음|역|저자)$")

_WIKI_403_WARNED = False


def _wiki_headers() -> dict[str, str]:
    ua = os.getenv("WIKI_USER_AGENT", "").strip()
    if not ua:
        ua = "BookJukSeeder/1.0 (mailto:your_email@example.com)"
    return {"User-Agent": ua, "Accept": "application/json"}


def parse_primary_author(authors_str: str) -> str:
    """정보나루 authors 문자열에서 주 저자 이름 추출.

    예) '헤르만 헤세;김역자 옮김' -> '헤르만 헤세'
        '지은이: 한강'           -> '한강'
        '홍길동 지음'             -> '홍길동'
    """
    if not authors_str:
        return ""
    # 첫 번째 토큰만 취함 (;,|(（ 기준)
    raw_name = re.split(r"[,;|（(]", authors_str)[0].strip()
    # '지은이: 이름' 같은 역할 접두어 제거
    author_name = _ROLE_PREFIX_RE.sub("", raw_name).strip()
    # '홍길동 지음' 같은 역할 접미어 제거
    author_name = _TRAILING_ROLE_RE.sub("", author_name).strip()
    return author_name


async def check_author_wiki(
    authors_str: str,
    client: httpx.AsyncClient,
    timeout: float = 10.0,
) -> tuple[bool, str | None, str]:
    """저자의 Wikipedia 페이지 존재 여부 확인.

    Returns:
        (has_wiki, wiki_lang, summary)
        - has_wiki: True이면 위키 페이지 있음
        - wiki_lang: 'ko' 또는 'en' 또는 None
        - summary: 저자 소개 (intro extract)
    """
    global _WIKI_403_WARNED

    author_name = parse_primary_author(authors_str)
    if not author_name:
        return False, None, ""

    for lang in ("ko", "en"):
        try:
            resp = await client.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "formatversion": "2",
                    "prop": "extracts",
                    "exintro": "1",
                    "explaintext": "1",
                    "redirects": "1",
                    "titles": author_name,
                },
                timeout=timeout,
                headers=_wiki_headers(),
            )
            if resp.status_code == 403:
                if not _WIKI_403_WARNED:
                    _WIKI_403_WARNED = True
                    print(
                        "[WARN] Wikipedia 403 차단됨.\n"
                        "       WIKI_USER_AGENT 환경변수를 '앱명/1.0 (mailto:이메일)' 형식으로 설정하거나\n"
                        "       네트워크 환경을 확인하세요. Wikipedia 데이터 수집이 비활성화됩니다."
                    )
                return False, None, ""
            resp.raise_for_status()
            data = resp.json()
            pages = data.get("query", {}).get("pages", [])
            if not pages:
                continue
            page = pages[0]
            if page.get("missing"):
                continue
            extract = str(page.get("extract") or "").strip()
            # 페이지는 있지만 extract가 비어있어도 위키 있는 것으로 간주
            return True, lang, extract
        except httpx.HTTPStatusError:
            continue
        except Exception:
            continue

    return False, None, ""
