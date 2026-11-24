"""Keyword retrieval using BM25."""

import re
from rank_bm25 import BM25Okapi
from chunking.models import Chunk


def _tokenize(text: str) -> list[str]:
    """Simple alphanumeric tokenizer suited for legal terms and clause numbers."""
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())


class BM25Store:
    """In-memory BM25 index over Chunk objects."""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.bm25: BM25Okapi | None = None

    def build(self, chunks: list[Chunk]) -> None:
        """Tokenize chunks and build BM25 index."""
        self.chunks = chunks
        corpus = [_tokenize(c.text) for c in chunks]
        self.bm25 = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        """Return top-k (Chunk, bm25_score) pairs."""
        if self.bm25 is None or not self.chunks:
            return []
        scores = self.bm25.get_scores(_tokenize(query))
        ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self.chunks[i], float(scores[i])) for i in ranked_idx]
