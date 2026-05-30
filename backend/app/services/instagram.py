"""Instagram Graph API client.

Requires the connected user to have a Facebook Page linked to an Instagram
Business or Creator account. The token here is a long-lived Page access token
exchanged from the Meta OAuth flow.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

GRAPH_BASE = "https://graph.facebook.com/v21.0"
MEDIA_FIELDS = (
    "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,"
    "like_count,comments_count"
)
INSIGHT_METRICS_MEDIA = "impressions,reach,saved,shares,plays,total_interactions"
INSIGHT_METRICS_ACCOUNT = "impressions,reach,profile_views,follower_count"


def exchange_code_for_token(client_id: str, client_secret: str, redirect_uri: str, code: str) -> Dict[str, Any]:
    with httpx.Client(timeout=30) as c:
        short = c.get(
            f"{GRAPH_BASE}/oauth/access_token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        ).json()
        if "access_token" not in short:
            return short
        long_lived = c.get(
            f"{GRAPH_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "fb_exchange_token": short["access_token"],
            },
        ).json()
        return long_lived


def get_ig_business_account(access_token: str) -> Optional[Dict[str, str]]:
    """Find the IG Business Account ID linked to one of the user's pages."""
    with httpx.Client(timeout=30) as c:
        pages = c.get(
            f"{GRAPH_BASE}/me/accounts",
            params={"access_token": access_token, "fields": "id,name,access_token,instagram_business_account"},
        ).json()
        for page in pages.get("data", []):
            iba = page.get("instagram_business_account")
            if iba:
                ig = c.get(
                    f"{GRAPH_BASE}/{iba['id']}",
                    params={"access_token": page["access_token"], "fields": "id,username,followers_count,media_count"},
                ).json()
                return {
                    "ig_user_id": iba["id"],
                    "username": ig.get("username", ""),
                    "page_id": page["id"],
                    "page_access_token": page["access_token"],
                    "followers_count": ig.get("followers_count", 0),
                    "media_count": ig.get("media_count", 0),
                }
        return None


def fetch_recent_media(ig_user_id: str, access_token: str, limit: int = 30) -> List[Dict[str, Any]]:
    with httpx.Client(timeout=30) as c:
        res = c.get(
            f"{GRAPH_BASE}/{ig_user_id}/media",
            params={"access_token": access_token, "fields": MEDIA_FIELDS, "limit": limit},
        ).json()
        return res.get("data", [])


def fetch_media_insights(media_id: str, access_token: str) -> Dict[str, int]:
    with httpx.Client(timeout=30) as c:
        res = c.get(
            f"{GRAPH_BASE}/{media_id}/insights",
            params={"access_token": access_token, "metric": INSIGHT_METRICS_MEDIA},
        ).json()
    out: Dict[str, int] = {}
    for item in res.get("data", []):
        try:
            out[item["name"]] = int(item["values"][0]["value"])
        except (KeyError, IndexError, ValueError, TypeError):
            continue
    return out


def fetch_account_insights(ig_user_id: str, access_token: str, days: int = 28) -> Dict[str, Any]:
    with httpx.Client(timeout=30) as c:
        res = c.get(
            f"{GRAPH_BASE}/{ig_user_id}/insights",
            params={
                "access_token": access_token,
                "metric": INSIGHT_METRICS_ACCOUNT,
                "period": "day",
                "metric_type": "total_value",
            },
        ).json()
        return res


def parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
    except Exception:
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None
