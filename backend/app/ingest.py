"""
Ingest pipeline: text → chunks → embeddings → Qdrant (dense + sparse BM25 vectors).
"""
import re
import uuid
import httpx
from typing import List, Dict, Any

from qdrant_client.models import PointStruct, SparseVector
from app.config import (
    OLLAMA_URL, EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP,
    COLLECTION_NAME, VECTOR_SIZE,
)
from app.qdrant_client import get_client


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping character-level chunks."""
    chunks: List[str] = []
    start = 0
    text = text.strip()
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# Embedding via Ollama
# ---------------------------------------------------------------------------

async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Batch embed texts using Ollama nomic-embed-text."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        vectors = []
        for text in texts:
            resp = await client.post(
                f"{OLLAMA_URL}/api/embed",
                json={"model": EMBED_MODEL, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            vectors.append(data["embeddings"][0])
        return vectors


# ---------------------------------------------------------------------------
# BM25 sparse vector (TF-IDF-style term weights)
# ---------------------------------------------------------------------------

def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def build_sparse_vector(text: str, vocab: Dict[str, int]) -> SparseVector:
    """Build a simple TF-based sparse vector using a shared vocabulary."""
    tokens = tokenize(text)
    tf: Dict[int, float] = {}
    for t in tokens:
        if t in vocab:
            idx = vocab[t]
            tf[idx] = tf.get(idx, 0.0) + 1.0
    # Normalize by doc length
    total = max(sum(tf.values()), 1)
    indices = list(tf.keys())
    values = [v / total for v in tf.values()]
    return SparseVector(indices=indices, values=values)


def build_vocab(all_chunks: List[str]) -> Dict[str, int]:
    """Assign integer IDs to every unique token across all chunks."""
    vocab: Dict[str, int] = {}
    idx = 0
    for chunk in all_chunks:
        for token in tokenize(chunk):
            if token not in vocab:
                vocab[token] = idx
                idx += 1
    return vocab


# ---------------------------------------------------------------------------
# Upsert to Qdrant
# ---------------------------------------------------------------------------

async def upsert_chunks(
    chunks: List[str],
    doc_id: str,
    filename: str,
    vocab: Dict[str, int],
) -> int:
    """Embed chunks and upsert to Qdrant with dense + sparse vectors."""
    dense_vecs = await embed_texts(chunks)
    client = get_client()

    points: List[PointStruct] = []
    for i, (chunk, dense) in enumerate(zip(chunks, dense_vecs)):
        sparse = build_sparse_vector(chunk, vocab)
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={"": dense, "bm25": sparse},
                payload={
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": i,
                    "text": chunk,
                },
            )
        )

    await client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


# ---------------------------------------------------------------------------
# Full ingest entry point
# ---------------------------------------------------------------------------

async def ingest_document(text: str, filename: str) -> Dict[str, Any]:
    """Chunk, embed, and index a single document. Returns ingest stats."""
    # Derive doc_id from filename (strip extension)
    doc_id = filename.rsplit(".", 1)[0]

    chunks = chunk_text(text)
    vocab = build_vocab(chunks)

    n = await upsert_chunks(chunks, doc_id, filename, vocab)
    return {
        "doc_id": doc_id,
        "filename": filename,
        "chunks": n,
        "chunk_size": CHUNK_SIZE,
        "overlap": CHUNK_OVERLAP,
    }
