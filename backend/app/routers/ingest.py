"""Ingest router: upload text files → chunk → embed → Qdrant."""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.ingest import ingest_document
from app.config import SYNTHETIC_DOCS_DIR

router = APIRouter()


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """Upload a text file and index it into Qdrant."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")

    result = await ingest_document(text, file.filename)
    return {"status": "indexed", **result}


@router.post("/ingest/preload")
async def preload_synthetic_docs():
    """Load all synthetic docs from disk into Qdrant (called on first run)."""
    results = []
    if not os.path.isdir(SYNTHETIC_DOCS_DIR):
        raise HTTPException(status_code=500, detail="synthetic_docs directory not found")

    for fname in sorted(os.listdir(SYNTHETIC_DOCS_DIR)):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(SYNTHETIC_DOCS_DIR, fname)
        with open(fpath, encoding="utf-8") as f:
            text = f.read()
        result = await ingest_document(text, fname)
        results.append(result)

    return {"status": "preloaded", "documents": results}
