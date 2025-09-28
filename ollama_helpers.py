import os
import json
import time
import requests

# --- Ollama API setup (using bakllava:7b everywhere) ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "bakllava:7b")
GEN_URL = os.getenv("OLLAMA_URL_GENERATE", "http://127.0.0.1:11434/api/generate")
CHAT_URL = os.getenv("OLLAMA_URL_CHAT", "http://127.0.0.1:11434/v1/chat/completions")

# Retry settings
MAX_RETRIES = 5       # how many times to retry
RETRY_DELAY = 15      # seconds between retries


# --- Helpers ---
def clean_markdown_json(text: str) -> str:
    """Remove markdown fences (```json ... ```), so JSON loads cleanly."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
        return t.replace("```json", "").replace("```", "")
    return t


def _ollama_generate_json(prompt: str, images=None) -> dict:
    """Call Ollama to generate JSON using /api/generate, fallback to chat if needed."""
    for attempt in range(MAX_RETRIES):
        try:
            payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
            if images:
                payload["images"] = images

            r = requests.post(GEN_URL, json=payload, timeout=120)
            if r.status_code == 200:
                raw = (r.json().get("response") or "").strip()
                if raw:
                    return json.loads(clean_markdown_json(raw))

        except Exception as e:
            print(f"[Ollama generate failed] attempt {attempt+1}/{MAX_RETRIES}: {e}")

        # wait before retrying
        time.sleep(RETRY_DELAY)

    # Fallback: /v1/chat/completions
    for attempt in range(MAX_RETRIES):
        try:
            msg = [{"role": "user", "content": prompt}]
            if images:
                msg[0]["images"] = images

            r = requests.post(
                CHAT_URL,
                json={"model": OLLAMA_MODEL, "messages": msg, "stream": False},
                timeout=120,
            )
            if r.status_code == 200:
                j = r.json()
                raw = j["choices"][0]["message"]["content"].strip()
                if raw:
                    return json.loads(clean_markdown_json(raw))
        except Exception as e:
            print(f"[Ollama chat failed] attempt {attempt+1}/{MAX_RETRIES}: {e}")

        time.sleep(RETRY_DELAY)

    return {}


# --- Public API ---
def ollama_generate(prompt: str, images=None, stream: bool = False, timeout: int = 120) -> str:
    """General text generation using bakllava:7b, with retries if warming up."""
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": stream}
    if images:
        payload["images"] = images

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(GEN_URL, json=payload, timeout=timeout, stream=stream)
            r.raise_for_status()

            if stream:
                output = []
                for line in r.iter_lines():
                    if line:
                        try:
                            js = json.loads(line.decode("utf-8"))
                            chunk = js.get("response", "")
                            if chunk:
                                output.append(chunk)
                        except Exception:
                            continue
                return "".join(output).strip()
            else:
                js = r.json()
                return (js.get("response") or "").strip()

        except Exception as e:
            print(f"[Ollama error] attempt {attempt+1}/{MAX_RETRIES}: {e}")
            time.sleep(RETRY_DELAY)

    return "[Ollama error] Failed after multiple retries. Model may still be warming up."


def ask_for_category_mapping(column_name: str, values: list) -> dict:
    """
    Ask bakllava:7b locally to return a JSON dict for normalizing categories.
    Example: raw 'severity' → {"low": "Low", "med": "Medium", ...}
    """
    if not values:
        return {}

    prompt = (
        f"You are a data cleaning assistant for NDIS incident data. "
        f"Return a JSON dictionary mapping each raw '{column_name}' value "
        f"to a normalized category. Return ONLY valid JSON.\n\n"
        f"Values:\n" + "\n".join(f"- {v}" for v in values[:120])
    )

    result = _ollama_generate_json(prompt)
    return result if isinstance(result, dict) else {}
