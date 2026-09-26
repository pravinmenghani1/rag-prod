# RAG Portal — Production-Grade RAG System

A full-stack RAG (Retrieval-Augmented Generation) system with:

- **Hybrid Search**: BM25 (sparse) + Semantic (dense) retrieval fused with Reciprocal Rank Fusion
- **Reranker**: Cross-encoder (`ms-marco-MiniLM-L-6-v2`) for precision reranking
- **Metrics**: Recall@K, Precision@K, nDCG@K against ground truth
- **LLM**: Ollama `llama3.1` for response generation (streamed)
- **Portal**: React + Vite + Tailwind with live SSE pipeline trace

---

## Architecture

```
User Query
    │
    ▼
Hybrid Retrieval (BM25 + Semantic via Qdrant)
    │
    ▼
RRF Fusion (Reciprocal Rank Fusion)
    │
    ▼
Metrics (Recall@K, Precision@K, nDCG@K vs. ground truth)
    │
    ▼
Reranker (cross-encoder/ms-marco-MiniLM-L-6-v2)
    │
    ▼
LLM (Ollama llama3.1, streamed)
    │
    ▼
Portal (SSE live trace of each stage)
```

---

## Prerequisites

- Docker + Docker Compose
- [Ollama](https://ollama.ai) running locally with these models pulled:
  ```bash
  ollama pull nomic-embed-text   # embeddings
  ollama pull llama3.1           # generation
  ```
- Node.js ≥18 (for frontend dev server)

---

## Quick Start

### 1. Start Qdrant + Backend

```bash
cd rag-prod
docker-compose up --build
```

Backend API will be available at `http://localhost:8000`.

### 2. Start Frontend (dev mode)

```bash
cd frontend
npm install
npm run dev
```

Portal will be at `http://localhost:5173`.

---

## Running the Backend Locally (without Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## Using the Portal

1. **Load Documents**: Click "🚀 Load Synthetic Docs" to index the 6 pre-built synthetic documents into Qdrant. Or upload your own `.txt` files.

2. **Ask a Query**: Type a question or click an example query button.

3. **Watch the Pipeline**: The Pipeline Trace panel shows each stage live:
   - 🧠 Semantic search results
   - 📊 BM25 search results  
   - 🔀 Fused (RRF) ranking
   - 📈 Retrieval metrics (Precision@K, Recall@K, nDCG@K)
   - ✅ Reranked top chunks
   - 🤖 LLM response (streamed token by token)

---

## Synthetic Documents

6 pre-built documents covering:
- `doc_climate.txt` — Introduction to Climate Change
- `doc_ml.txt` — Fundamentals of Machine Learning
- `doc_quantum.txt` — Quantum Computing Explained
- `doc_nutrition.txt` — Nutrition and Human Health
- `doc_internet.txt` — History of the Internet
- `doc_space.txt` — Space Exploration: Past, Present, Future

Ground truth relevance for 8 example queries is in `backend/app/synthetic_docs/ground_truth.json`.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + Qdrant status |
| POST | `/api/ingest` | Upload and index a `.txt` file |
| POST | `/api/ingest/preload` | Load all synthetic docs |
| POST | `/api/query` | SSE stream of full RAG pipeline |

### Query Request
```json
POST /api/query
{
  "query": "What causes climate change?",
  "top_k": 5,
  "rerank_top_n": 3
}
```

### SSE Event Types
```
{ "type": "stage", "stage": "query_received", "message": "...", "query": "..." }
{ "type": "stage", "stage": "retrieval_semantic", "results": [...] }
{ "type": "stage", "stage": "retrieval_bm25", "results": [...] }
{ "type": "stage", "stage": "retrieval_fused", "results": [...] }
{ "type": "stage", "stage": "metrics", "precision_at_k": 0.8, "recall_at_k": 1.0, "ndcg_at_k": 0.92 }
{ "type": "stage", "stage": "reranking_done", "results": [...] }
{ "type": "token", "token": "Climate" }
{ "type": "stage", "stage": "done", "full_response": "..." }
```

---

## Configuration

Edit `backend/app/config.py` to tune:
- `CHUNK_SIZE` / `CHUNK_OVERLAP` — document chunking
- `TOP_K` — number of candidates retrieved per method
- `RERANK_TOP_N` — chunks passed to LLM after reranking
- `LLM_MODEL` — swap to `mistral:7b`, `gemma3:4b`, etc.
