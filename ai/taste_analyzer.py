from openai import AsyncOpenAI

from clustering import TasteCluster


def _build_cluster_description(cluster: TasteCluster, idx: int) -> str:
    book_titles = ", ".join(f"<{b.title}>" for b in cluster.books)

    kw_str = ", ".join(f"{w}({s:.1f})" for w, s in cluster.top_keywords)

    kdc_str = ", ".join(f"{name}({cnt}권)" for name, cnt in cluster.kdc_distribution.items())

    return (
        f"[취향 그룹 {idx + 1}] ({len(cluster.books)}권)\n"
        f"  도서: {book_titles}\n"
        f"  핵심 키워드(가중치 합산): {kw_str}\n"
        f"  KDC 분류 분포: {kdc_str}"
    )


def build_analysis_prompt(clusters: list[TasteCluster]) -> str:
    cluster_texts = "\n\n".join(
        _build_cluster_description(c, i) for i, c in enumerate(clusters)
    )

    return f"""아래는 한 사용자가 최근에 읽은 책들을 분석한 결과입니다.
책들의 키워드를 벡터화하고 클러스터링하여 취향 그룹을 자동으로 분리했습니다.

{cluster_texts}

위 데이터를 바탕으로 이 사용자의 독서 취향을 분석해주세요.

규칙:
1. 각 취향 그룹별로 어떤 관심사를 가지고 있는지 구체적으로 설명
2. 그룹이 여러 개라면 각 그룹 간의 공통점이나 연결고리도 분석
3. 전체적으로 이 독자가 어떤 사람인지 성향을 추론
4. 친근하고 자연스러운 한국어로 작성
5. 전체 분량은 3~5문장"""


async def analyze_taste(
    openai_client: AsyncOpenAI,
    clusters: list[TasteCluster],
    model: str = "gpt-4o",
) -> str:
    prompt = build_analysis_prompt(clusters)

    resp = await openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "당신은 독서 취향 분석 전문가입니다. 사용자의 독서 데이터를 기반으로 취향을 정확하고 통찰력 있게 분석합니다.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=1024,
    )

    return resp.choices[0].message.content or ""
