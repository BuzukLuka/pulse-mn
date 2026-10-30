"""Gemini API-н нимгэн клиент (REST). SDK шаардахгүй."""
import json
import re

import requests
from django.conf import settings

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def is_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)


def generate_json(prompt: str, timeout: int = 30) -> dict:
    resp = requests.post(
        URL.format(model=settings.GEMINI_MODEL),
        headers={"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)


def embed(text: str, timeout: int = 20):
    """Утгын вектор (semantic embedding). Алдаа гарвал None."""
    url = "https://generativelanguage.googleapis.com/v1beta/models/{m}:embedContent".format(m=settings.GEMINI_EMBED_MODEL)
    r = requests.post(url, headers={"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"},
                      json={"content": {"parts": [{"text": text[:8000]}]}, "taskType": "SEMANTIC_SIMILARITY"},
                      timeout=timeout)
    r.raise_for_status()
    return r.json()["embedding"]["values"]
