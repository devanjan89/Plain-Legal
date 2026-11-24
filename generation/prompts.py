"""Prompt templates and red-flag checklist for Plain Legal."""

from chunking.models import Chunk

REFUSAL_PHRASE = "This document doesn't seem to cover that."

SYSTEM_PROMPT = f"""You are Plain Legal, a document reading assistant that explains legal and policy documents in simple, everyday English.

STRICT RULES:
1. Answer ONLY using the provided clauses below. Do not use outside knowledge or guess.
2. Cite the exact clause number(s) in your answer (for example: "Under Clause 2.3...").
3. Use short, plain-language sentences that a non-lawyer can easily understand.
4. If the provided clauses do not contain enough information to answer the question, reply with EXACTLY:
{REFUSAL_PHRASE}
"""

RED_FLAG_QUESTIONS: list[tuple[str, str]] = [
    ("Auto-renewal", "Does this document automatically renew, and what are the terms or price changes on renewal?"),
    ("Penalties & Late Fees", "What penalties, late fees, or fines apply under this document?"),
    ("Termination Rights", "How can either party terminate or cancel this agreement early?"),
    ("Data Sharing & Privacy", "Does this document allow sharing personal data with third parties?"),
    ("Deposit & Refund Terms", "What are the security deposit, payment, or refund rules and timelines?"),
    ("Notice Periods", "What notice periods are required for termination, renewal, or changes?"),
]


def build_user_prompt(question: str, chunks: list[Chunk]) -> str:
    """Format retrieved clauses and the user question into a grounded prompt."""
    context_blocks = []
    for c in chunks:
        context_blocks.append(
            f"[Clause {c.clause_number} | Page {c.page_number} | {c.heading}]\n{c.text}"
        )
    context = "\n\n".join(context_blocks)
    return f"CLAUSES:\n{context}\n\nQUESTION: {question}\n\nPLAIN-LANGUAGE ANSWER:"
