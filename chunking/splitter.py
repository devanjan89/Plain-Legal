"""Clause-aware and fixed-size chunking strategies."""

import re
from ingestion.pdf_loader import PageContent
from chunking.models import Chunk

# Matches headings like "Section 4. Termination", "ARTICLE 2: Fees", "Part III - Eligibility"
HEADING_RE = re.compile(
    r"^(?:section|article|clause|part|chapter)\s+[0-9ivxlcdm]+(?:\.[0-9]+)?\b[.:\-\s]*(.*)$",
    re.IGNORECASE,
)

# Matches numbered clauses like "1.1 ...", "7(a) ...", "Clause 4.2 ..."
CLAUSE_RE = re.compile(
    r"^(?:clause\s+)?(?P<num>\d+(?:\.\d+)+(?:\([a-z0-9]+\))?|\d+\([a-z0-9]+\))\b[.:\-\s]+(?P<body>.+)$",
    re.IGNORECASE,
)


def chunk_fixed(
    pages: list[PageContent],
    chunk_size: int = 600,
    overlap: int = 100,
) -> list[Chunk]:
    """Split each page into fixed-size character chunks with overlap."""
    chunks: list[Chunk] = []
    counter = 0

    for page in pages:
        text = page.text
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            piece = text[start:end].strip()
            if piece:
                counter += 1
                chunks.append(
                    Chunk(
                        chunk_id=f"fixed_{counter}",
                        text=piece,
                        clause_number=f"Chunk {counter}",
                        heading=f"Page {page.page_number}",
                        page_number=page.page_number,
                        source=page.source,
                    )
                )
            if end == len(text):
                break
            start = max(0, end - overlap)

    return chunks


def chunk_by_clause(
    pages: list[PageContent],
    fallback_chunk_size: int = 600,
    fallback_overlap: int = 100,
) -> list[Chunk]:
    """
    Split pages on headings and numbered clauses (e.g., Section 2, 2.1, 7(a)).
    Falls back to fixed-size chunking if no clause structure is detected.
    """
    chunks: list[Chunk] = []
    current_heading = "General"
    current_clause_num: str | None = None
    current_lines: list[str] = []
    current_page = pages[0].page_number if pages else 1
    source = pages[0].source if pages else "unknown"
    counter = 0

    def flush() -> None:
        nonlocal counter, current_lines, current_clause_num
        if current_clause_num and current_lines:
            counter += 1
            body = " ".join(current_lines).strip()
            full_text = f"[{current_heading} | Clause {current_clause_num}] {body}"
            chunks.append(
                Chunk(
                    chunk_id=f"clause_{counter}",
                    text=full_text,
                    clause_number=current_clause_num,
                    heading=current_heading,
                    page_number=current_page,
                    source=source,
                )
            )
        current_lines = []
        current_clause_num = None

    for page in pages:
        for raw_line in page.text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            heading_match = HEADING_RE.match(line)
            clause_match = CLAUSE_RE.match(line)

            if heading_match and not clause_match:
                flush()
                current_heading = line
                current_page = page.page_number
                continue

            if clause_match:
                flush()
                current_clause_num = clause_match.group("num")
                current_page = page.page_number
                current_lines = [clause_match.group("body").strip()]
                continue

            if current_clause_num is not None:
                current_lines.append(line)

    flush()

    # Fallback when document has no recognizable numbered clauses
    if len(chunks) < 2:
        return chunk_fixed(pages, chunk_size=fallback_chunk_size, overlap=fallback_overlap)

    return chunks


def chunk_pages(
    pages: list[PageContent],
    strategy: str = "clause",
    chunk_size: int = 600,
    overlap: int = 100,
) -> list[Chunk]:
    """Switchable entry point: strategy='clause' or strategy='fixed'."""
    if strategy == "clause":
        return chunk_by_clause(pages, fallback_chunk_size=chunk_size, fallback_overlap=overlap)
    if strategy == "fixed":
        return chunk_fixed(pages, chunk_size=chunk_size, overlap=overlap)
    raise ValueError(f"Unknown chunking strategy: {strategy}")


if __name__ == "__main__":
    import sys
    from ingestion.pdf_loader import load_pdf

    if len(sys.argv) < 2:
        print("Usage: python -m chunking.splitter <path_to_pdf> [clause|fixed]")
        sys.exit(1)

    strategy = sys.argv[2] if len(sys.argv) > 2 else "clause"
    pages = load_pdf(sys.argv[1])
    chunks = chunk_pages(pages, strategy=strategy)
    print(f"Strategy={strategy} -> {len(chunks)} chunks\n")
    for c in chunks[:6]:
        print(f"  [{c.clause_number} | p.{c.page_number} | {c.heading}] {c.text[:110]}...")
