"""Streamlit UI for Plain Legal."""

import os
import sys
import os
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
import streamlit as st

from ingestion.pdf_loader import load_pdf
from chunking.splitter import chunk_pages
from retrieval.hybrid import HybridRetriever
from generation.llm import generate_answer
from generation.prompts import RED_FLAG_QUESTIONS, REFUSAL_PHRASE

st.set_page_config(page_title="Plain Legal", page_icon="📄", layout="wide")

st.title("Plain Legal")
st.caption("Upload a rental agreement, terms of service, or government scheme PDF and ask questions in plain English.")
st.info(
    "**Disclaimer:** Plain Legal explains document text in simple language for informational purposes only. "
    "It is **not** legal advice.",
    icon="ℹ️",
)

with st.sidebar:
    st.header("Settings")
    chunk_strategy = st.selectbox("Chunking strategy", ["clause", "fixed"], index=0)
    retrieval_mode = st.selectbox("Retrieval mode", ["hybrid", "dense"], index=0)
    top_k = st.slider("Top-K clauses", min_value=1, max_value=10, value=5)
    ollama_model = st.text_input("Ollama model", value=os.getenv("OLLAMA_MODEL", "llama3.2:3b"))

uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])


@st.cache_resource(show_spinner="Indexing document...")
def build_index(file_bytes: bytes, file_name: str, strategy: str):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)
    try:
        pages = load_pdf(tmp_path)
        for p in pages:
            p.source = file_name
        chunks = chunk_pages(pages, strategy=strategy)
        retriever = HybridRetriever()
        retriever.index(chunks)
        return retriever, len(pages), len(chunks)
    finally:
        tmp_path.unlink(missing_ok=True)


if uploaded_file is not None:
    retriever, num_pages, num_chunks = build_index(
        uploaded_file.getvalue(), uploaded_file.name, chunk_strategy
    )
    st.success(f"Indexed **{uploaded_file.name}** ({num_pages} pages, {num_chunks} chunks using `{chunk_strategy}` strategy).")

    question = st.text_input(
        "Ask a question about this document:",
        placeholder="e.g., Can the landlord raise rent mid-lease?",
    )

    col1, col2 = st.columns([1, 1])
    ask_clicked = col1.button("Ask", type="primary")
    red_flags_clicked = col2.button("Check for red flags")

    if ask_clicked and question.strip():
        with st.spinner("Searching clauses and generating answer..."):
            hits = retriever.search(question, top_k=top_k, mode=retrieval_mode)
            chunks = [c for c, _ in hits]
            try:
                answer = generate_answer(question, chunks, model=ollama_model)
            except Exception as exc:
                st.error(f"LLM call failed (is Ollama running with `{ollama_model}`?): {exc}")
                st.stop()

        st.subheader("Answer")
        st.write(answer)

        with st.expander(f"Source clauses ({len(hits)} retrieved)"):
            for chunk, score in hits:
                st.markdown(f"**Clause {chunk.clause_number}** — Page {chunk.page_number} ({chunk.heading}) | score: `{score:.4f}`")
                st.write(chunk.text)
                st.divider()

    if red_flags_clicked:
        st.subheader("Red Flag Check")
        for label, rf_question in RED_FLAG_QUESTIONS:
            hits = retriever.search(rf_question, top_k=top_k, mode=retrieval_mode)
            chunks = [c for c, _ in hits]
            try:
                ans = generate_answer(rf_question, chunks, model=ollama_model)
            except Exception as exc:
                st.error(f"LLM call failed: {exc}")
                break

            status = "⚪ Not covered" if REFUSAL_PHRASE.lower() in ans.lower() else "🚩 Found"
            with st.expander(f"{status} — {label}", expanded=(status.startswith("🚩"))):
                st.write(ans)
                st.caption("Sources: " + ", ".join(f"Clause {c.clause_number} (p.{c.page_number})" for c in chunks[:3]))
