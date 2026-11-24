"""Data models for document chunks."""

from dataclasses import dataclass


@dataclass
class Chunk:
    """A retrievable unit of text with structural metadata."""
    chunk_id: str
    text: str
    clause_number: str
    heading: str
    page_number: int
    source: str
