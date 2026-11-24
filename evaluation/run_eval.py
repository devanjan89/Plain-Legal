"""Evaluate chunking (fixed vs clause) x retrieval (dense vs hybrid) + refusal accuracy."""

import argparse
import json
from pathlib import Path

from ingestion.pdf_loader import load_pdf
from chunking.splitter import chunk_pages
from retrieval.hybrid import HybridRetriever
from generation.llm import generate_answer
from generation.prompts import REFUSAL_PHRASE


def clause_hit(chunk_text: str, clause_number: str, expected_clause: str) -> bool:
    """Check if the retrieved chunk matches or contains the expected clause."""
    if clause_number.strip().lower() == expected_clause.strip().lower():
        return True
    return f"{expected_clause} " in chunk_text or f"Clause {expected_clause}" in chunk_text


def evaluate_config(
    dataset: list[dict],
    docs_dir: Path,
    strategy: str,
    mode: str,
    run_refusal_llm: bool = False,
) -> dict[str, float]:
    """Compute Hit@1, Hit@3, Hit@5, and optional refusal accuracy."""
    retrievers: dict[str, HybridRetriever] = {}
    for doc_name in sorted({row["doc"] for row in dataset}):
        pages = load_pdf(docs_dir / doc_name)
        chunks = chunk_pages(pages, strategy=strategy)
        retriever = HybridRetriever()
        retriever.index(chunks)
        retrievers[doc_name] = retriever

    answerable = [r for r in dataset if r["answerable"]]
    unanswerable = [r for r in dataset if not r["answerable"]]

    hits = {1: 0, 3: 0, 5: 0}
    for row in answerable:
        results = retrievers[row["doc"]].search(row["question"], top_k=5, mode=mode)
        for k in (1, 3, 5):
            if any(clause_hit(c.text, c.clause_number, row["expected_clause"]) for c, _ in results[:k]):
                hits[k] += 1

    refusal_acc = float("nan")
    if run_refusal_llm and unanswerable:
        correct_refusals = 0
        for row in unanswerable:
            results = retrievers[row["doc"]].search(row["question"], top_k=5, mode=mode)
            ans = generate_answer(row["question"], [c for c, _ in results])
            if REFUSAL_PHRASE.lower() in ans.lower():
                correct_refusals += 1
        refusal_acc = correct_refusals / len(unanswerable)

    n = len(answerable) or 1
    return {
        "hit@1": hits[1] / n,
        "hit@3": hits[3] / n,
        "hit@5": hits[5] / n,
        "refusal": refusal_acc,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-llm", action="store_true", help="Also evaluate LLM refusal rate via Ollama")
    args = parser.parse_args()

    dataset = json.loads(Path("evaluation/dataset.json").read_text(encoding="utf-8"))
    docs_dir = Path("data/samples")

    configs = [
        ("fixed", "dense"),
        ("fixed", "hybrid"),
        ("clause", "dense"),
        ("clause", "hybrid"),
    ]

    print("| Chunking | Retrieval | Hit@1 | Hit@3 | Hit@5 | Refusal Acc |")
    print("| :--- | :--- | :---: | :---: | :---: | :---: |")
    for strategy, mode in configs:
        m = evaluate_config(dataset, docs_dir, strategy, mode, run_refusal_llm=args.with_llm)
        ref_str = f"{m['refusal']*100:.0f}%" if m["refusal"] == m["refusal"] else "n/a (use --with-llm)"
        print(
            f"| {strategy} | {mode} | {m['hit@1']*100:.1f}% | {m['hit@3']*100:.1f}% | {m['hit@5']*100:.1f}% | {ref_str} |"
        )


if __name__ == "__main__":
    main()
