from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Post, SocialAccount, User
from ..security import decrypt_token, get_current_user
from ..services import instagram as ig
from ..services import ai

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _ig_account(db: Session, user: User) -> SocialAccount:
    acc = (
        db.query(SocialAccount)
        .filter(SocialAccount.user_id == user.id, SocialAccount.platform == "instagram")
        .first()
    )
    if not acc:
        raise HTTPException(400, "Connect Instagram first")
    return acc


@router.post("/instagram/sync")
def sync_instagram(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    acc = _ig_account(db, user)
    token = decrypt_token(acc.access_token_enc)
    media = ig.fetch_recent_media(acc.platform_user_id, token, limit=30)
    synced = 0
    for m in media:
        existing = (
            db.query(Post)
            .filter(Post.user_id == user.id, Post.platform == "instagram", Post.platform_post_id == m["id"])
            .first()
        )
        insights = ig.fetch_media_insights(m["id"], token)
        row_data = dict(
            user_id=user.id,
            platform="instagram",
            platform_post_id=m["id"],
            caption=m.get("caption", "") or "",
            media_type=m.get("media_type", ""),
            media_url=m.get("media_url", "") or m.get("thumbnail_url", "") or "",
            permalink=m.get("permalink", ""),
            likes=int(m.get("like_count") or 0),
            comments=int(m.get("comments_count") or 0),
            reach=int(insights.get("reach", 0)),
            impressions=int(insights.get("impressions", 0)),
            saves=int(insights.get("saved", 0)),
            shares=int(insights.get("shares", 0)),
            plays=int(insights.get("plays", 0)),
            posted_at=ig.parse_timestamp(m.get("timestamp")),
            fetched_at=datetime.utcnow(),
        )
        if existing:
            for k, v in row_data.items():
                setattr(existing, k, v)
        else:
            db.add(Post(**row_data))
        synced += 1
    db.commit()
    return {"synced": synced}


@router.get("/instagram/overview")
def overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    acc = _ig_account(db, user)
    posts = (
        db.query(Post)
        .filter(Post.user_id == user.id, Post.platform == "instagram")
        .order_by(Post.posted_at.desc().nullslast())
        .limit(30)
        .all()
    )
    total_reach = sum(p.reach for p in posts)
    total_impr = sum(p.impressions for p in posts)
    total_likes = sum(p.likes for p in posts)
    total_comments = sum(p.comments for p in posts)
    avg_reach = total_reach / len(posts) if posts else 0
    engagement_rate = (
        ((total_likes + total_comments) / total_reach * 100) if total_reach else 0
    )
    top = sorted(posts, key=lambda p: p.reach, reverse=True)[:5]
    return {
        "handle": acc.handle,
        "followers": (acc.extra or {}).get("followers_count", 0),
        "posts_analyzed": len(posts),
        "totals": {
            "reach": total_reach,
            "impressions": total_impr,
            "likes": total_likes,
            "comments": total_comments,
        },
        "avg_reach": round(avg_reach, 1),
        "engagement_rate": round(engagement_rate, 2),
        "top_posts": [
            {
                "id": p.id,
                "caption": (p.caption or "")[:160],
                "permalink": p.permalink,
                "media_url": p.media_url,
                "reach": p.reach,
                "likes": p.likes,
                "comments": p.comments,
                "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            }
            for p in top
        ],
    }


@router.get("/instagram/best-times")
def best_times(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ig_account(db, user)
    posts = (
        db.query(Post)
        .filter(Post.user_id == user.id, Post.platform == "instagram", Post.posted_at.isnot(None))
        .all()
    )
    buckets: Dict[str, List[int]] = {}
    for p in posts:
        key = f"{p.posted_at.strftime('%a')}-{p.posted_at.hour:02d}"
        buckets.setdefault(key, []).append(p.reach)
    rows = [
        {"slot": k, "avg_reach": round(sum(v) / len(v), 1), "n": len(v)}
        for k, v in buckets.items()
    ]
    rows.sort(key=lambda r: r["avg_reach"], reverse=True)
    return {"slots": rows[:10]}


@router.get("/instagram/hashtags")
def hashtag_perf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ig_account(db, user)
    posts = (
        db.query(Post)
        .filter(Post.user_id == user.id, Post.platform == "instagram")
        .all()
    )
    perf: Dict[str, List[int]] = {}
    counts: Counter = Counter()
    for p in posts:
        cap = p.caption or ""
        tags = [t.lower() for t in cap.split() if t.startswith("#") and len(t) > 1]
        for t in tags:
            perf.setdefault(t, []).append(p.reach)
            counts[t] += 1
    rows = [
        {"tag": t, "avg_reach": round(sum(v) / len(v), 1), "uses": counts[t]}
        for t, v in perf.items()
        if counts[t] >= 2
    ]
    rows.sort(key=lambda r: r["avg_reach"], reverse=True)
    return {"hashtags": rows[:25]}


@router.post("/advice")
def advice(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    posts = (
        db.query(Post)
        .filter(Post.user_id == user.id, Post.platform == "instagram")
        .order_by(Post.posted_at.desc().nullslast())
        .limit(30)
        .all()
    )
    if not posts:
        raise HTTPException(400, "Sync Instagram first")
    payload = [
        {
            "caption": (p.caption or "")[:200],
            "reach": p.reach,
            "likes": p.likes,
            "comments": p.comments,
            "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            "media_type": p.media_type,
        }
        for p in posts
    ]
    return ai.engagement_advice(user.niche, payload)
