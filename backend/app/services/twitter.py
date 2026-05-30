"""X (Twitter) API v2 client using app-only Bearer Token for trend/search reads."""
from typing import Any, Dict, List

import httpx

from ..config import get_settings

BASE = "https://api.twitter.com"


def _headers() -> Dict[str, str]:
    s = get_settings()
    if not s.X_BEARER_TOKEN:
        raise RuntimeError("X_BEARER_TOKEN not configured")
    return {"Authorization": f"Bearer {s.X_BEARER_TOKEN}"}


def search_recent(query: str, max_results: int = 25) -> List[Dict[str, Any]]:
    with httpx.Client(timeout=30, headers=_headers()) as c:
        res = c.get(
            f"{BASE}/2/tweets/search/recent",
            params={
                "query": query,
                "max_results": max_results,
                "tweet.fields": "public_metrics,created_at,lang",
            },
        )
        if res.status_code >= 400:
            return []
        return res.json().get("data", [])


def trending_for_woeid(woeid: int = 1) -> List[Dict[str, Any]]:
    """Trending topics. WOEID 1 = worldwide. Requires elevated/Basic+ access."""
    with httpx.Client(timeout=30, headers=_headers()) as c:
        res = c.get(f"{BASE}/1.1/trends/place.json", params={"id": woeid})
        if res.status_code >= 400:
            return []
        data = res.json()
        if isinstance(data, list) and data:
            return data[0].get("trends", [])
        return []
