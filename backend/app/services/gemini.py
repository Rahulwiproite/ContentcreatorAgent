"""Google Gemini provider with structured output for reliable JSON."""
import json
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings

BASE = "https://generativelanguage.googleapis.com/v1beta"


IDEAS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "ideas": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "hook": {"type": "STRING"},
                    "script_outline": {"type": "STRING"},
                    "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "suggested_time": {"type": "STRING"},
                    "virality_score": {"type": "NUMBER"},
                },
                "required": ["title", "hook", "script_outline", "hashtags", "suggested_time", "virality_score"],
            },
        }
    },
    "required": ["ideas"],
}


ADVICE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "best_times": {"type": "ARRAY", "items": {"type": "STRING"}},
        "actions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "why": {"type": "STRING"},
                    "do_this": {"type": "STRING"},
                },
                "required": ["title", "why", "do_this"],
            },
        },
    },
    "required": ["summary", "best_times", "actions"],
}


FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
]


class RateLimitError(RuntimeError):
    """Gemini free tier daily/minute quota exhausted across all fallback models."""


def _call_once(
    model: str, body: Dict[str, Any], api_key: str
) -> tuple[int, Dict[str, Any] | str]:
    url = f"{BASE}/models/{model}:generateContent"
    with httpx.Client(timeout=90) as c:
        res = c.post(url, params={"key": api_key}, json=body)
        if res.status_code == 200:
            return 200, res.json()
        return res.status_code, res.text[:500]


def generate(
    system: str,
    prompt: str,
    model: str,
    max_tokens: int = 12000,
    temperature: float = 0.95,
    json_mode: bool = True,
    schema: Optional[Dict[str, Any]] = None,
) -> str:
    s = get_settings()
    if not s.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    gen_cfg: Dict[str, Any] = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
        "thinkingConfig": {"thinkingBudget": 0},
    }
    if json_mode:
        gen_cfg["responseMimeType"] = "application/json"
        if schema is not None:
            gen_cfg["responseSchema"] = schema
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": gen_cfg,
    }

    # Try preferred model first, then fall back through the list when 429-rate-limited.
    tried: List[str] = []
    candidates = [model] + [m for m in FALLBACK_MODELS if m != model]
    last_error = ""
    for m in candidates:
        tried.append(m)
        status, payload = _call_once(m, body, s.GEMINI_API_KEY)
        if status == 200 and isinstance(payload, dict):
            try:
                return payload["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                last_error = f"unexpected response shape from {m}"
                continue
        if status == 429:
            last_error = f"429 quota exceeded on {m}"
            continue
        # other errors (auth/perm) won't be fixed by switching model -- give up
        raise RuntimeError(f"Gemini error {status} on {m}: {payload}")

    raise RateLimitError(
        f"Gemini free tier quota exhausted on all models tried: {', '.join(tried)}. "
        "Wait a few minutes (per-minute reset) or until midnight Pacific (daily reset), "
        "or add billing to your Google AI Studio key for higher limits."
    )
