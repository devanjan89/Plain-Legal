"""Hybrid retriever combining FAISS embeddings and BM25 via Reciprocal Rank Fusion."""

from chunking.models import Chunk
from retrieval.vector_store import VectorStore, DEFAULT_EMBED_MODEL
from retrieval.bm25_store import BM25Store


def reciprocal_rank_fusion(
    rankings: list[list[tuple[Chunk, float]]],
    k: int = 60,
    top_k: int = 5,
) -> list[tuple[Chunk, float]]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion (RRF):
    score(doc) = sum(1 / (k + rank))
    """
    scores: dict[str, float] = {}
    chunk_map: dict[str, Chunk] = {}

    for ranking in rankings:
        for rank, (chunk, _raw_score) in enumerate(ranking, start=1):
            chunk_map[chunk.chunk_id] = chunk
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)

    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)[:top_k]
    return [(chunk_map[cid], scores[cid]) for cid in sorted_ids]


class HybridRetriever:
    """Supports both dense-only and hybrid (dense + BM25 + RRF) retrieval."""

    def __init__(self, model_name: str = DEFAULT_EMBED_MODEL) -> None:
        self.vector_store = VectorStore(model_name=model_name)
        self.bm25_store = BM25Store()

    def index(self, chunks: list[Chunk]) -> None:
        """Build both vector and BM25 indexes."""
        self.vector_store.build(chunks)
        self.bm25_store.build(chunks)

    def search(self, query: str, top_k: int = 5, mode: str = "hybrid") -> list[tuple[Chunk, float]]:
        """
        Retrieve top-k chunks.
        Args:
            query: User question.
            top_k: Number of chunks to return (default 5).
            mode: 'hybrid' (dense + BM25 + RRF) or 'dense' (embeddings only).
        """
        if mode == "dense":
            return self.vector_store.search(query, top_k=top_k)
        if mode == "hybrid":
            fetch_k = max(top_k * 2, 10)
            dense_hits = self.vector_store.search(query, top_k=fetch_k)
            bm25_hits = self.bm25_store.search(query, top_k=fetch_k)
            return reciprocal_rank_fusion([dense_hits, bm25_hits], top_k=top_k)
        raise ValueError(f"Unknown retrieval mode: {mode}")


if __name__ == "__main__":
    import sys
    from ingestion.pdf_loader import load_pdf
    from chunking.splitter import chunk_pages

    if len(sys.argv) < 3:
        print("Usage: python -m retrieval.hybrid <path_to_pdf> <question>")
        sys.exit(1)

    pages = load_pdf(sys.argv[1])
    chunks = chunk_pages(pages, strategy="clause")
    retriever = HybridRetriever()
    retriever.index(chunks)
    hits = retriever.search(sys.argv[2], top_k=5, mode="hybrid")
    for rank, (chunk, score) in enumerate(hits, start=1):
        print(f"{rank}. [Clause {chunk.clause_number} | p.{chunk.page_number} | RRF={score:.4f}] {chunk.text[:140]}...")
