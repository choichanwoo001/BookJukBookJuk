"""북적북적 하이브리드 추천 엔진

Knowledge Graph + RippleNet + Hybrid Scoring + XAI 를 결합한
4단계 추천 파이프라인.

빠른 시작:
    from hybrid_recommender import HybridRecommenderPipeline, UserProfile

    pipeline = HybridRecommenderPipeline.from_env()
    await pipeline.add_books(isbn_list=["9788937460470", "9788936434120"])
    pipeline.user_profile.add_read("9788937460470", "채식주의자")
    results = await pipeline.recommend(top_k=5)
"""
from .pipeline import HybridRecommenderPipeline
from .phase3_scoring.user_profile import UserProfile, UserAction, ActionType
from .phase4_xai.explainer import ExplainedRecommendation

__all__ = [
    "HybridRecommenderPipeline",
    "UserProfile",
    "UserAction",
    "ActionType",
    "ExplainedRecommendation",
]
