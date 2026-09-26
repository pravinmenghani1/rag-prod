import os

# Qdrant
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME: str = "rag_docs"
VECTOR_SIZE: int = 768  # nomic-embed-text output dimension

# Ollama
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.1:latest")

# Chunking
CHUNK_SIZE: int = 400        # characters
CHUNK_OVERLAP: int = 80      # characters

# Retrieval
TOP_K: int = 5               # candidates per method before fusion
RERANK_TOP_N: int = 3        # chunks sent to LLM after reranking

# Paths
SYNTHETIC_DOCS_DIR: str = os.path.join(os.path.dirname(__file__), "synthetic_docs")
GROUND_TRUTH_PATH: str = os.path.join(SYNTHETIC_DOCS_DIR, "ground_truth.json")
