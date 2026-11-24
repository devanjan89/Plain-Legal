# Plain Legal

A from-scratch, framework-free RAG application in Python that explains rental agreements, terms of service, and government scheme PDFs in plain English, with exact clause citations and strict refusal when a document does not cover a question.

> **Disclaimer:** Plain Legal explains document text in simple language for informational purposes only. It is not legal advice.

## Features

- **Layout-aware PDF ingestion:** Extracts text per page with PyMuPDF and strips repeated headers, footers, and standalone page numbers using bounding-box positions.
- **Switchable chunking:** Splits documents on headings and numbered clauses (`Section 4`, `1.1`, `Clause 7(a)`) with an automatic fallback to fixed-size overlapping chunks when no structure is detected.
- **Hybrid retrieval:** Combines local dense embeddings (`BAAI/bge-small-en-v1.5` + FAISS) and BM25 keyword search (`rank_bm25`) using Reciprocal Rank Fusion (RRF).
- **Grounded generation:** Uses a single swappable LLM wrapper (defaulting to local `llama3.2:3b` via Ollama) that cites clause numbers and replies `"This document doesn't seem to cover that."` when the context does not support an answer.
- **Streamlit UI & Red Flag scanner:** Supports PDF upload, Q&A with expandable source clauses, and a one-click red-flag check covering auto-renewal, penalties, termination rights, data sharing, deposits/refunds, and notice periods.

## Architecture

```text
PDF Upload
  -> ingestion/pdf_loader.py     (PyMuPDF block extraction + margin header/footer stripping)
  -> chunking/splitter.py        (Clause-aware regex splitter + fixed-size overlap fallback)
  -> retrieval/hybrid.py         (FAISS + bge-small-en-v1.5 AND BM25 merged via RRF)
  -> generation/llm.py           (Single swappable LLM wrapper -> local Ollama llama3.2:3b)
  -> app/streamlit_app.py        (Q&A, expandable source clauses, Red Flag scanner)
```

## Quick Start (Local)

1. **Install Ollama and pull the model**
   ```bash
   ollama pull llama3.2:3b
   ```

2. **Set up the Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Generate sample PDFs and verify the pipeline**
   ```bash
   python data/create_sample_pdfs.py
   python verify_pipeline.py
   ```

4. **Launch the Streamlit app**
   ```bash
   streamlit run app/streamlit_app.py
   ```
   Open `http://localhost:8501` in your browser.

## Docker Deployment

Run both the Streamlit app and Ollama together using Docker Compose:

```bash
docker compose up --build -d
docker exec -it plain-legal-ollama ollama pull llama3.2:3b
```

Open `http://localhost:8501` in your browser. To stop the containers:

```bash
docker compose down
```

*(Note: The `Dockerfile` installs CPU-only PyTorch and pre-downloads `BAAI/bge-small-en-v1.5` during build to keep image size down and startup fast.)*

## Evaluation

Evaluated on `evaluation/dataset.json` (24 questions across 3 public-style documents: a residential rental agreement, a terms of service, and PM-KISAN guidelines, including 4 unanswerable questions).

Re-run the benchmark:
```bash
python -m evaluation.run_eval --with-llm
```

| Chunking | Retrieval | Hit@1 | Hit@3 | Hit@5 | Refusal Acc |
| :--- | :--- | :---: | :---: | :---: | :---: |
| fixed | dense | 70.0% | 100.0% | 100.0% | 100% |
| fixed | hybrid | 80.0% | 100.0% | 100.0% | 100% |
| clause | dense | 85.0% | 100.0% | 100.0% | 100% |
| clause | hybrid | 95.0% | 100.0% | 100.0% | 100% |

**Takeaway:** Switching from fixed-size chunks + dense search to clause-aware chunking + hybrid search (BM25 + RRF) improved **Hit@1 from 70.0% to 95.0%**, while maintaining **100% Hit@5** and **100% refusal accuracy** on unanswerable queries.

## Known Limitations

- **Scanned PDFs:** PyMuPDF reads digital text layers only; image-only scans require an OCR step (such as Tesseract).
- **Complex tables:** Multi-column fee schedules or annexure tables can lose row/column alignment and would benefit from `pdfplumber` table extraction.
- **Benchmark scale:** The 24-question test set uses short, clean 2–3 page sample PDFs. Longer real-world contracts (30+ pages) would benefit from a cross-encoder reranker and a similarity-score threshold before calling the LLM.
- **Small local LLM:** `llama3.2:3b` is fast and runs locally for free, but larger models (swappable in `generation/llm.py`) handle nuanced legal phrasing more reliably.