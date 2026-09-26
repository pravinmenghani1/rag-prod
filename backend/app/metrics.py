"""
IR metrics: Recall@K, Precision@K, nDCG@K.
Evaluated against ground truth from ground_truth.json.
"""
import json
import math
from typing import List, Dict, Any, Optional

from app.config import GROUND_TRUTH_PATH


def load_ground_truth() -> Dict[str, Any]:
    with open(GROUND_TRUTH_PATH) as f:
        return json.load(f)


def find_ground_truth(query: str) -> Optional[Dict[str, Any]]:
    """Find the closest matching ground truth entry for a query (exact match first)."""
    gt = load_ground_truth()
    query_lower = query.strip().lower()
    for entry in gt["queries"]:
        if entry["query"].strip().lower() == query_lower:
            return entry
    # Fuzzy: check keyword overlap
    query_tokens = set(query_lower.split())
    best_entry = None
    best_overlap = 0
    for entry in gt["queries"]:
        entry_tokens = set(entry["query"].lower().split())
        overlap = len(query_tokens & entry_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_entry = entry
    return best_entry if best_overlap >= 2 else None


def precision_at_k(retrieved_doc_ids: List[str], relevant_doc_ids: List[str], k: int) -> float:
    top_k = retrieved_doc_ids[:k]
    relevant_set = set(relevant_doc_ids)
    hits = sum(1 for d in top_k if d in relevant_set)
    return hits / k if k > 0 else 0.0


def recall_at_k(retrieved_doc_ids: List[str], relevant_doc_ids: List[str], k: int) -> float:
    top_k = retrieved_doc_ids[:k]
    relevant_set = set(relevant_doc_ids)
    hits = sum(1 for d in top_k if d in relevant_set)
    return hits / len(relevant_set) if relevant_set else 0.0


def dcg_at_k(retrieved_doc_ids: List[str], relevant_doc_ids: List[str], k: int) -> float:
    relevant_set = set(relevant_doc_ids)
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_doc_ids[:k]):
        if doc_id in relevant_set:
            dcg += 1.0 / math.log2(i + 2)  # log2(rank+1), rank is 1-indexed
    return dcg


def ndcg_at_k(retrieved_doc_ids: List[str], relevant_doc_ids: List[str], k: int) -> float:
    actual_dcg = dcg_at_k(retrieved_doc_ids, relevant_doc_ids, k)
    # Ideal DCG: all relevant docs at the top
    ideal_dcg = dcg_at_k(relevant_doc_ids, relevant_doc_ids, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def compute_metrics(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    k: int = 5,
) -> Dict[str, Any]:
    """
    Compute retrieval metrics against ground truth.
    retrieved_chunks: list of dicts with at least 'doc_id'.
    """
    gt_entry = find_ground_truth(query)
    if gt_entry is None:
        return {
            "ground_truth_found": False,
            "precision_at_k": None,
            "recall_at_k": None,
            "ndcg_at_k": None,
            "k": k,
        }

    retrieved_doc_ids = [c.get("doc_id", "") for c in retrieved_chunks]
    relevant_doc_ids = gt_entry["relevant_doc_ids"]

    p_k = precision_at_k(retrieved_doc_ids, relevant_doc_ids, k)
    r_k = recall_at_k(retrieved_doc_ids, relevant_doc_ids, k)
    n_k = ndcg_at_k(retrieved_doc_ids, relevant_doc_ids, k)

    return {
        "ground_truth_found": True,
        "query_id": gt_entry["id"],
        "relevant_doc_ids": relevant_doc_ids,
        "retrieved_doc_ids": retrieved_doc_ids[:k],
        "precision_at_k": round(p_k, 4),
        "recall_at_k": round(r_k, 4),
        "ndcg_at_k": round(n_k, 4),
        "k": k,
    }
