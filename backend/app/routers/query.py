"""
Query router: SSE streaming endpoint that emits each pipeline stage as it completes.

Event flow:
  stage: query_received
  stage: retrieval_semantic
  stage: retrieval_bm25
  stage: retrieval_fused
  stage: metrics
  stage: reranking
  stage: llm_start
  token: <token> (one per LLM token)
  stage: done
  stage: error (if any stage fails)
"""
import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.retrieval import hybrid_search
from app.reranker import rerank
from app.metrics import compute_metrics
from app.llm import stream_llm_response
from app.config import TOP_K, RERANK_TOP_N

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    top_k: int = TOP_K
    rerank_top_n: int = RERANK_TOP_N


def sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


async def run_pipeline(query: str, top_k: int, rerank_top_n: int) -> AsyncGenerator[str, None]:
    try:
        # Stage 1: Query received
        yield sse_event("stage", {
            "stage": "query_received",
            "message": f"Query received: '{query}'",
            "query": query,
        })

        # Stage 2: Hybrid retrieval
        yield sse_event("stage", {
            "stage": "retrieval_running",
            "message": "Running hybrid search (BM25 + semantic)...",
        })

        search_results = await hybrid_search(query, top_k=top_k)

        yield sse_event("stage", {
            "stage": "retrieval_semantic",
            "message": f"Semantic search returned {len(search_results['semantic'])} results",
            "results": search_results["semantic"],
        })

        yield sse_event("stage", {
            "stage": "retrieval_bm25",
            "message": f"BM25 search returned {len(search_results['bm25'])} results",
            "results": search_results["bm25"],
        })

        fused = search_results["fused"]
        yield sse_event("stage", {
            "stage": "retrieval_fused",
            "message": f"RRF fusion produced {len(fused)} ranked candidates",
            "results": [
                {
                    "rank": i + 1,
                    "rrf_score": c["rrf_score"],
                    "doc_id": c.get("doc_id", ""),
                    "text": c.get("text", "")[:200] + "..." if len(c.get("text", "")) > 200 else c.get("text", ""),
                }
                for i, c in enumerate(fused)
            ],
        })

        # Stage 3: Metrics
        metrics = compute_metrics(query, fused, k=top_k)
        yield sse_event("stage", {
            "stage": "metrics",
            "message": "Computed retrieval metrics against ground truth",
            **metrics,
        })

        # Stage 4: Reranking
        yield sse_event("stage", {
            "stage": "reranking_start",
            "message": f"Reranking top {len(fused)} chunks with cross-encoder...",
        })

        reranked = rerank(query, fused, top_n=rerank_top_n)

        yield sse_event("stage", {
            "stage": "reranking_done",
            "message": f"Reranked to top {len(reranked)} chunks",
            "results": [
                {
                    "rank": i + 1,
                    "rerank_score": c.get("rerank_score", 0),
                    "doc_id": c.get("doc_id", ""),
                    "text": c.get("text", "")[:200] + "..." if len(c.get("text", "")) > 200 else c.get("text", ""),
                }
                for i, c in enumerate(reranked)
            ],
        })

        # Stage 5: LLM generation
        yield sse_event("stage", {
            "stage": "llm_start",
            "message": "Sending context to LLM, streaming response...",
            "context_chunks": len(reranked),
        })

        full_response = []
        async for token in stream_llm_response(query, reranked):
            full_response.append(token)
            yield sse_event("token", {"token": token})

        yield sse_event("stage", {
            "stage": "done",
            "message": "Pipeline complete",
            "full_response": "".join(full_response),
        })

    except Exception as e:
        yield sse_event("stage", {
            "stage": "error",
            "message": str(e),
        })


@router.post("/query")
async def query_pipeline(request: QueryRequest):
    """SSE endpoint streaming each RAG pipeline stage."""
    return StreamingResponse(
        run_pipeline(request.query, request.top_k, request.rerank_top_n),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
