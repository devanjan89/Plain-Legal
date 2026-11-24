"""Quick end-to-end check for Ingestion -> Chunking -> Hybrid Retrieval."""

from pathlib import Path
from ingestion.pdf_loader import load_pdf
from chunking.splitter import chunk_pages
from retrieval.hybrid import HybridRetriever


def main() -> None:
    sample_pdf = Path("data/samples/sample_rental_agreement.pdf")
    if not sample_pdf.exists():
        raise FileNotFoundError(
            f"{sample_pdf} not found. Run `python data/create_sample_pdfs.py` first."
        )

    print("1/3 Loading and cleaning PDF...")
    pages = load_pdf(sample_pdf)
    print(f"    Loaded {len(pages)} pages.")

    print("2/3 Splitting into clauses...")
    chunks = chunk_pages(pages, strategy="clause")
    print(f"    Created {len(chunks)} clause chunks.")

    print("3/3 Indexing and running hybrid search...")
    retriever = HybridRetriever()
    retriever.index(chunks)
    question = "Can the landlord raise rent mid-lease?"
    hits = retriever.search(question, top_k=3, mode="hybrid")

    print(f"\nQuery: {question}")
    for rank, (chunk, score) in enumerate(hits, start=1):
        print(f"  {rank}. [Clause {chunk.clause_number} | p.{chunk.page_number} | RRF={score:.4f}] {chunk.text[:120]}...")


if __name__ == "__main__":
    main()
