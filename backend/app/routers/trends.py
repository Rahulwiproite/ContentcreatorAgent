from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import TrendCache, User
from ..security import get_current_user
from ..services import twitter as tw

router = APIRouter(prefix="/trends", tags=["trends"])


def _read_cache(db: Session, platform: str, max_age_min: int = 180) -> Dict[str, Any] | None:
    row = (
        db.query(TrendCache)
        .filter(TrendCache.platform == platform)
        .order_by(TrendCache.refreshed_at.desc())
        .first()
    )
    if not row:
        return None
    if datetime.utcnow() - row.refreshed_at > timedelta(minutes=max_age_min):
        return None
    return row.payload


def _write_cache(db: Session, platform: str, payload: Dict[str, Any]) -> None:
    db.add(TrendCache(platform=platform, payload=payload, refreshed_at=datetime.utcnow()))
    db.commit()


def refresh_twitter_trends(db: Session) -> Dict[str, Any]:
    trends = tw.trending_for_woeid(1)
    funny_terms = ["comedy", "meme", "lol", "funny", "joke"]
    tweets = []
    for term in funny_terms:
        tweets.extend(tw.search_recent(f"{term} -is:retweet lang:en", max_results=10))
    tweets.sort(key=lambda t: (t.get("public_metrics", {}) or {}).get("like_count", 0), reverse=True)
    payload = {
        "trending": [{"name": t.get("name"), "volume": t.get("tweet_volume")} for t in trends[:25]],
        "top_funny_tweets": [
            {
                "text": t.get("text", "")[:280],
                "likes": (t.get("public_metrics", {}) or {}).get("like_count", 0),
                "retweets": (t.get("public_metrics", {}) or {}).get("retweet_count", 0),
            }
            for t in tweets[:15]
        ],
        "refreshed_at": datetime.utcnow().isoformat(),
    }
    _write_cache(db, "twitter", payload)
    return payload


@router.get("/all")
def all_trends(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    twitter = _read_cache(db, "twitter") or {}
    if not twitter:
        try:
            twitter = refresh_twitter_trends(db)
        except Exception as e:
            twitter = {"error": str(e), "trending": [], "top_funny_tweets": []}
    return {"twitter": twitter}


@router.post("/refresh")
def refresh(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        twitter = refresh_twitter_trends(db)
    except Exception as e:
        twitter = {"error": str(e)}
    return {"twitter": twitter}
