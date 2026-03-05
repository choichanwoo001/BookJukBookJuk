import asyncio
from collections import defaultdict

import numpy as np
from openai import AsyncOpenAI

from library_api import BookInfo, BookKeyword

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
MAX_BATCH_SIZE = 100


async def embed_texts(
    client: AsyncOpenAI,
    texts: list[str],
) -> dict[str, np.ndarray]:
    if not texts:
        return {}

    batches: list[list[str]] = []
    for i in range(0, len(texts), MAX_BATCH_SIZE):
        batches.append(texts[i : i + MAX_BATCH_SIZE])

    async def _embed_batch(batch: list[str]) -> list[tuple[str, np.ndarray]]:
        resp = await client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        return [
            (batch[item.index], np.array(item.embedding, dtype=np.float32))
            for item in resp.data
        ]

    tasks = [_embed_batch(batch) for batch in batches]
    batch_results = await asyncio.gather(*tasks)

    mapping: dict[str, np.ndarray] = {}
    for results in batch_results:
        for text, vec in results:
            mapping[text] = vec
    return mapping


def collect_unique_keywords(books: list[BookInfo]) -> list[str]:
    unique: set[str] = set()
    for book in books:
        for kw in book.keywords:
            unique.add(kw.word)
    return list(unique)


def build_book_vector(
    keywords: list[BookKeyword],
    word_vectors: dict[str, np.ndarray],
) -> np.ndarray | None:
    vectors: list[np.ndarray] = []
    weights: list[float] = []

    for kw in keywords:
        vec = word_vectors.get(kw.word)
        if vec is not None:
            vectors.append(vec)
            weights.append(kw.weight)

    if not vectors:
        return None

    weight_arr = np.array(weights, dtype=np.float32)
    weight_arr /= weight_arr.sum()

    stacked = np.stack(vectors)
    weighted_avg = (stacked.T @ weight_arr).T

    norm = np.linalg.norm(weighted_avg)
    if norm > 0:
        weighted_avg /= norm

    return weighted_avg


async def build_all_book_vectors(
    openai_client: AsyncOpenAI,
    books: list[BookInfo],
) -> list[tuple[BookInfo, np.ndarray]]:
    unique_words = collect_unique_keywords(books)
    word_vectors = await embed_texts(openai_client, unique_words)

    result: list[tuple[BookInfo, np.ndarray]] = []
    for book in books:
        vec = build_book_vector(book.keywords, word_vectors)
        if vec is not None:
            result.append((book, vec))
        else:
            print(f"[WARN] '{book.title}' 벡터 생성 실패 (키워드 없음)")
    return result
