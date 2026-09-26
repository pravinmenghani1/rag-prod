from fastapi import APIRouter
from app.qdrant_client import get_client
from app.config import COLLECTION_NAME

router = APIRouter()


@router.get("/health")
async def health():
    try:
        client = get_client()
        collections = await client.get_collections()
        names = [c.name for c in collections.collections]
        return {
            "status": "ok",
            "qdrant": "connected",
            "collection_ready": COLLECTION_NAME in names,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
