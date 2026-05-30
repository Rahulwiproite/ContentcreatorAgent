"""Facebook Pages: list pages and pull simple Page insights."""
from typing import Any, Dict, List

import httpx

GRAPH_BASE = "https://graph.facebook.com/v21.0"


def list_pages(access_token: str) -> List[Dict[str, Any]]:
    with httpx.Client(timeout=30) as c:
        res = c.get(
            f"{GRAPH_BASE}/me/accounts",
            params={"access_token": access_token, "fields": "id,name,access_token,fan_count,category"},
        ).json()
        return res.get("data", [])


def page_insights(page_id: str, page_access_token: str) -> Dict[str, Any]:
    metrics = "page_impressions,page_post_engagements,page_fans"
    with httpx.Client(timeout=30) as c:
        return c.get(
            f"{GRAPH_BASE}/{page_id}/insights",
            params={"access_token": page_access_token, "metric": metrics, "period": "days_28"},
        ).json()
