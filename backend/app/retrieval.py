"""
Hybrid retrieval: semantic (dense) + BM25 (sparse) fused via Reciprocal Rank Fusion.
"""
import re
import httpx
from typing import List, Dict, Any, Tuple

from qdrant_client.models import (
    SparseVector,
    SearchRequest,
    NamedVector,
    NamedSparseVector,
)
from app.config import OLLAMA_URL, EMBED_MODEL, COLLECTION_NAME, TOP_K
from app.qdrant_client import get_client
from app.ingest import tokenize


# ---------------------------------------------------------------------------
# Query embedding
# ---------------------------------------------------------------------------

async def embed_query(query: str) -> List[float]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": query},
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]


# ---------------------------------------------------------------------------
# BM25 query sparse vector
# ---------------------------------------------------------------------------

async def build_query_sparse_vector(query: str) -> SparseVector:
    """
    Build a sparse vector for the query using the collection's vocabulary.
    We fetch a small sample of points to reconstruct vocab indices from their
    sparse vectors, then map query tokens to those indices.
    """
    client = get_client()
    # Scroll a sample of points to discover the vocabulary mapping
    points, _ = await client.scroll(
        collection_name=COLLECTION_NAME,
        limit=200,
        with_vectors=["bm25"],
        with_payload=["text"],
    )

    # Rebuild token→index mapping from stored sparse vectors + texts
    token_to_idx: Dict[str, int] = {}
    for pt in points:
        if pt.vector and "bm25" in pt.vector:
            text = pt.payload.get("text", "")
            tokens = tokenize(text)
            sparse = pt.vector["bm25"]
            # sparse is a SparseVector with .indices and .values
            indices = sparse.indices if hasattr(sparse, "indices") else sparse.get("indices", [])
            for i, token in enumerate(set(tokens)):
                if i < len(indices):
                    token_to_idx[token] = indices[i]

    query_tokens = tokenize(query)
    tf: Dict[int, float] = {}
    for t in query_tokens:
        if t in token_to_idx:
            idx = token_to_idx[t]
            tf[idx] = tf.get(idx, 0.0) + 1.0

    if not tf:
        # Fallback: empty sparse vector
        return SparseVector(indices=[], values=[])

    indices = list(tf.keys())
    values = list(tf.values())
    return SparseVector(indices=indices, values=values)


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[str, float, Dict]]],
    k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Fuse multiple ranked lists using RRF.
    Each element in ranked_lists is a list of (point_id, score, payload).
    """
    scores: Dict[str, float] = {}
    payloads: Dict[str, Dict] = {}

    for ranked in ranked_lists:
        for rank, (pid, score, payload) in enumerate(ranked):
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (k + rank + 1)
            payloads[pid] = payload

    # Sort by fused score descending
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [
        {"id": pid, "rrf_score": scores[pid], **payloads[pid]}
        for pid in sorted_ids
    ]


# ---------------------------------------------------------------------------
# Full hybrid search
# ---------------------------------------------------------------------------

async def hybrid_search(query: str, top_k: int = TOP_K) -> Dict[str, Any]:
    """
    Run semantic + BM25 search, fuse with RRF.
    Returns detailed results for portal display.
    """
    client = get_client()

    # 1. Dense semantic search
    dense_vec = await embed_query(query)
    semantic_results = await client.search(
        collection_name=COLLECTION_NAME,
        query_vector=NamedVector(name="", vector=dense_vec),
        limit=top_k,
        with_payload=True,
    )

    # 2. Sparse BM25 search
    sparse_vec = await build_query_sparse_vector(query)
    if sparse_vec.indices:
        bm25_results = await client.search(
            collection_name=COLLECTION_NAME,
            query_vector=NamedSparseVector(name="bm25", vector=sparse_vec),
            limit=top_k,
            with_payload=True,
        )
    else:
        bm25_results = []

    # 3. Format individual result lists
    def fmt(results) -> List[Tuple[str, float, Dict]]:
        return [
            (
                str(r.id),
                float(r.score),
                {
                    "text": r.payload.get("text", ""),
                    "doc_id": r.payload.get("doc_id", ""),
                    "filename": r.payload.get("filename", ""),
                    "chunk_index": r.payload.get("chunk_index", 0),
                },
            )
            for r in results
        ]

    semantic_list = fmt(semantic_results)
    bm25_list = fmt(bm25_results)

    # 4. RRF fusion
    fused = reciprocal_rank_fusion([semantic_list, bm25_list])

    return {
        "semantic": [
            {"rank": i + 1, "score": s, "text": p["text"], "doc_id": p["doc_id"]}
            for i, (_, s, p) in enumerate(semantic_list)
        ],
        "bm25": [
            {"rank": i + 1, "score": s, "text": p["text"], "doc_id": p["doc_id"]}
            for i, (_, s, p) in enumerate(bm25_list)
        ],
        "fused": fused[:top_k],
    }
