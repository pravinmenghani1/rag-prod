"""Qdrant async client wrapper."""
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
)
from app.config import QDRANT_URL, COLLECTION_NAME, VECTOR_SIZE

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=QDRANT_URL)
    return _client


async def ensure_collection() -> None:
    """Create collection with dense + sparse vectors if it doesn't exist."""
    client = get_client()
    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if COLLECTION_NAME not in names:
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            sparse_vectors_config={
                "bm25": SparseVectorParams(index=SparseIndexParams(on_disk=False))
            },
        )
        print(f"[Qdrant] Created collection '{COLLECTION_NAME}'")
    else:
        print(f"[Qdrant] Collection '{COLLECTION_NAME}' already exists")
