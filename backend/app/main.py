import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import ingest, query, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure Qdrant collection exists."""
    from app.qdrant_client import ensure_collection
    await ensure_collection()
    yield


app = FastAPI(
    title="RAG Production API",
    description="Hybrid search RAG with BM25 + Semantic, reranker, metrics, and SSE streaming.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(query.router, prefix="/api", tags=["query"])
