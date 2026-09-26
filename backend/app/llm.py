"""
LLM client: streams a response from Ollama llama3.1 given a query + context chunks.
"""
import json
from typing import List, Dict, AsyncGenerator

import httpx
from app.config import OLLAMA_URL, LLM_MODEL


SYSTEM_PROMPT = """You are a helpful, accurate assistant. Answer the user's question using ONLY the provided context chunks. If the answer is not in the context, say "I don't have enough information to answer that."

Be concise, factual, and cite which document the information comes from when relevant."""


def build_prompt(query: str, chunks: List[Dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        doc_id = chunk.get("doc_id", "unknown")
        text = chunk.get("text", "")
        context_parts.append(f"[Chunk {i} from {doc_id}]\n{text}")

    context = "\n\n".join(context_parts)
    return f"Context:\n{context}\n\nQuestion: {query}"


async def stream_llm_response(
    query: str,
    chunks: List[Dict],
) -> AsyncGenerator[str, None]:
    """Async generator that yields tokens from Ollama as they arrive."""
    prompt = build_prompt(query, chunks)

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_URL}/api/chat",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
