"""
Reranker: uses a cross-encoder to reorder retrieved chunks.
Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (loaded once at startup).
"""
from typing import List, Dict, Any
from functools import lru_cache

from sentence_transformers import CrossEncoder
from app.config import RERANK_TOP_N

_cross_encoder: CrossEncoder | None = None


def get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        print("[Reranker] Loading cross-encoder/ms-marco-MiniLM-L-6-v2 ...")
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        print("[Reranker] Model loaded.")
    return _cross_encoder


def rerank(query: str, candidates: List[Dict[str, Any]], top_n: int = RERANK_TOP_N) -> List[Dict[str, Any]]:
    """
    Score (query, chunk) pairs with the cross-encoder and return top_n.
    Each candidate must have a 'text' field.
    """
    if not candidates:
        return []

    model = get_cross_encoder()
    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs).tolist()

    for c, score in zip(candidates, scores):
        c["rerank_score"] = round(float(score), 4)

    reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_n]
