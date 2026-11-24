"""PDF ingestion with header, footer, and page-number cleaning."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import pymupdf as fitz 


@dataclass
class PageContent:
    """Cleaned text and metadata for a single PDF page."""
    page_number: int
    text: str
    source: str


PAGE_NUM_PATTERN = re.compile(
    r"^\s*(?:page\s*\d+(?:\s*of\s*\d+)?|\d+\s*/\s*\d+|-\s*\d+\s*-|\d+)\s*$",
    re.IGNORECASE,
)


def _normalize_line(line: str) -> str:
    """Collapse whitespace and replace digits so 'Page 1' and 'Page 2' match."""
    line = re.sub(r"\d+", "#", line.strip())
    return re.sub(r"\s+", " ", line).lower()


def _detect_repeated_margin_lines(
    raw_pages: list[list[tuple[float, float, str]]],
    min_repeat_ratio: float = 0.5,
) -> set[str]:
    """Find normalized lines repeated in the top/bottom 10% across pages."""
    if len(raw_pages) < 2:
        return set()

    margin_counts: Counter[str] = Counter()
    for page_lines in raw_pages:
        seen_on_page: set[str] = set()
        for rel_y0, rel_y1, text in page_lines:
            if rel_y0 < 0.10 or rel_y1 > 0.90:
                norm = _normalize_line(text)
                if norm and norm not in seen_on_page:
                    margin_counts[norm] += 1
                    seen_on_page.add(norm)

    threshold = max(2, int(len(raw_pages) * min_repeat_ratio))
    return {line for line, count in margin_counts.items() if count >= threshold}


def load_pdf(pdf_path: str | Path) -> list[PageContent]:
    """Extract and clean text per page from a PDF file."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = fitz.open(path)
    raw_pages: list[list[tuple[float, float, str]]] = []

    try:
        for page in doc:
            page_height = page.rect.height or 1.0
            page_lines: list[tuple[float, float, str]] = []
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))

            for block in blocks:
                if block[6] != 0:
                    continue
                rel_y0 = block[1] / page_height
                rel_y1 = block[3] / page_height
                for line in block[4].splitlines():
                    cleaned = line.strip()
                    if cleaned:
                        page_lines.append((rel_y0, rel_y1, cleaned))
            raw_pages.append(page_lines)
    finally:
        doc.close()

    repeated_margins = _detect_repeated_margin_lines(raw_pages)
    results: list[PageContent] = []

    for idx, page_lines in enumerate(raw_pages, start=1):
        kept_lines: list[str] = []
        for rel_y0, rel_y1, text in page_lines:
            if PAGE_NUM_PATTERN.match(text):
                continue
            if (rel_y0 < 0.10 or rel_y1 > 0.90) and _normalize_line(text) in repeated_margins:
                continue
            kept_lines.append(text)

        cleaned_text = re.sub(r"\n{3,}", "\n\n", "\n".join(kept_lines)).strip()
        if cleaned_text:
            results.append(PageContent(page_number=idx, text=cleaned_text, source=path.name))

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m ingestion.pdf_loader <path_to_pdf>")
        sys.exit(1)

    pages = load_pdf(sys.argv[1])
    print(f"Loaded {len(pages)} pages from {sys.argv[1]}\n")
    for p in pages:
        print(f"--- Page {p.page_number} ({len(p.text)} chars) ---")
        print(p.text[:350], "\n")
