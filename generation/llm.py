"""Single swappable LLM interface (defaults to lightweight local Ollama)."""

import os
import requests
from chunking.models import Chunk
from generation.prompts import SYSTEM_PROMPT, build_user_prompt


def generate_answer(
    question: str,
    chunks: list[Chunk],
    model: str | None = None,
    provider: str | None = None,
) -> str:
    """
    Generate a grounded plain-language answer from retrieved chunks.
    Keep all provider logic here so swapping Ollama / OpenAI / Anthropic is one edit.
    """
    active_provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()
    user_prompt = build_user_prompt(question, chunks)

    if active_provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        active_model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        resp = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": active_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()

    raise ValueError(
        f"Unsupported LLM_PROVIDER='{active_provider}'. "
        "Default is 'ollama' (run `ollama pull llama3.2:3b`)."
    )
