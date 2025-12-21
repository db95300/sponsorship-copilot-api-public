from __future__ import annotations

import json
from typing import Any

import requests

from backend.app.core.config import settings


class LlmError(RuntimeError):
    pass


def ollama_generate_json(*, prompt: str) -> dict[str, Any]:
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": settings.ollama_temperature},
    }

    try:
        resp = requests.post(url, json=payload, timeout=90)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise LlmError(f"Ollama request failed: {exc}") from exc

    data = resp.json()
    raw = data.get("response", "")
    if not raw:
        raise LlmError("Ollama returned empty response.")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LlmError(f"Model did not return valid JSON. Raw: {raw[:200]}") from exc