"""Local dense retrieval using sentence-transformers + FAISS."""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from chunking.models import Chunk

DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"


class VectorStore:
    """In-memory FAISS cosine-similarity index over Chunk objects."""

    def __init__(self, model_name: str = DEFAULT_EMBED_MODEL) -> None:
        self.model = SentenceTransformer(model_name)
        self.chunks: list[Chunk] = []
        self.index: faiss.IndexFlatIP | None = None

    def build(self, chunks: list[Chunk]) -> None:
        """Embed all chunks and build an inner-product FAISS index (cosine on normalized vectors)."""
        self.chunks = chunks
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        vectors = np.asarray(embeddings, dtype="float32")
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        """Return top-k (Chunk, cosine_score) pairs for a query."""
        if self.index is None or not self.chunks:
            return []
        q_vec = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)
        q_vec = np.asarray(q_vec, dtype="float32")
        k = min(top_k, len(self.chunks))
        scores, indices = self.index.search(q_vec, k)
        return [(self.chunks[i], float(s)) for i, s in zip(indices[0], scores[0]) if i >= 0]
