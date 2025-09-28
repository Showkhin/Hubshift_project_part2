# ollama_helpers.py
import json
import os
from typing import List, Optional

import requests
import streamlit as st

def _ollama_base():
    if "OLLAMA_BASE_URL" in st.secrets:
        return st.secrets["OLLAMA_BASE_URL"].rstrip("/")
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")

def _ollama_model():
    if "OLLAMA_MODEL" in st.secrets:
        return st.secrets["OLLAMA_MODEL"]
    return os.getenv("OLLAMA_MODEL", "bakllava:7b")

def _gen_url():
    if "OLLAMA_URL_GENERATE" in st.secrets:
        return st.secrets["OLLAMA_URL_GENERATE"]
    return _ollama_base() + "/api/generate"

def ollama_generate(prompt: str, images: Optional[List[str]] = None, stream: bool = False, timeout: int = 120) -> str:
    url = _gen_url()
    payload = {"model": _ollama_model(), "prompt": prompt, "stream": stream}
    if images:
        payload["images"] = images
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        js = r.json()
        # /api/generate returns chunk(s). If server streams disabled, we get single object with 'response'.
        return js.get("response", "").strip()
    except Exception as e:
        return f"[Ollama error] {e}"

def ask_for_category_mapping(column_name: str, values: List[str]) -> dict:
    """
    Best-effort JSON mapping via LLM. Returns {} if the model can't supply a valid JSON object.
    """
    if not values:
        return {}
    prompt = (
        f"You are a data cleaning assistant for NDIS incident data. "
        f"Create a JSON dictionary mapping raw '{column_name}' values "
        f"to a short, normalized category. Return ONLY a JSON object, no explanations.\n\n"
        f"Values:\n" + "\n".join(f"- {v}" for v in values[:120])
    )
    raw = ollama_generate(prompt, images=None)
    try:
        start = raw.find("{"); end = raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start:end+1])
    except Exception:
        pass
    return {}
