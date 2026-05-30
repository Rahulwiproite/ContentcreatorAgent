"""No-auth agent endpoints. Implicit default user.
Live trend sources: Reddit (free, always on) + X (when token configured)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..default_user import get_default_user
from ..models import Idea, Post, TrendCache
from ..schemas import IdeaOut
from ..services import ai, reddit, twitter as tw
from ..services.ai import current_provider, list_categories, list_languages
from ..services.gemini import RateLimitError

router = APIRouter(prefix="/agent", tags=["agent"])


class StartRequest(BaseModel):
    niche: Optional[str] = None
    category: str = "general"
    language: str = "en"
    vibe: str = "relatable observational"
    count: int = 6
    platform: str = "instagram"


class StartResponse(BaseModel):
    niche: str
    category: str
    language: str
    provider: str
    sources: Dict[str, Any]
    ideas: List[IdeaOut]


class ScriptRequest(BaseModel):
    language: Optional[str] = None


class ScriptResponse(BaseModel):
    idea_id: int
    title: str
    script: str
    language: str


class StatusResponse(BaseModel):
    ready: bool
    provider: str
    niche: str
    categories: List[str]
    languages: List[Dict[str, str]]
    sources: Dict[str, Any]


def _x_available() -> bool:
    return bool(get_settings().X_BEARER_TOKEN)


def _fetch_trends(category: str, db: Session) -> Dict[str, Any]:
    """Always fresh Reddit pull; X if token; cache last results to TrendCache."""
    sources: Dict[str, Any] = {}

    try:
        reddit_data = reddit.trends_for(category)
        sources["reddit"] = {
            "live": True,
            "category": reddit_data["category"],
            "subs_scanned": reddit_data["subs_scanned"],
            "posts": reddit_data["top_posts"][:20],
        }
        db.add(TrendCache(platform="reddit", payload=reddit_data, refreshed_at=datetime.utcnow()))
    except Exception as e:
        sources["reddit"] = {"live": False, "error": str(e)[:160]}

    if _x_available():
        try:
            tweets = []
            for term in ["meme", "viral", "trending"]:
                tweets.extend(tw.search_recent(f"{term} -is:retweet lang:en", max_results=10))
            tweets.sort(key=lambda t: (t.get("public_metrics", {}) or {}).get("like_count", 0), reverse=True)
            sources["x"] = {
                "live": True,
                "top_tweets": [
                    {
                        "text": t.get("text", "")[:240],
                        "likes": (t.get("public_metrics", {}) or {}).get("like_count", 0),
                        "retweets": (t.get("public_metrics", {}) or {}).get("retweet_count", 0),
                    }
                    for t in tweets[:12]
                ],
            }
            db.add(TrendCache(platform="x", payload=sources["x"], refreshed_at=datetime.utcnow()))
        except Exception as e:
            sources["x"] = {"live": False, "error": str(e)[:160]}
    else:
        sources["x"] = {"live": False, "reason": "X_BEARER_TOKEN not configured"}

    db.commit()
    return sources


def _top_posts(db: Session, user_id: int, n: int = 10) -> list[dict]:
    rows = (
        db.query(Post)
        .filter(Post.user_id == user_id)
        .order_by(Post.reach.desc())
        .limit(n)
        .all()
    )
    return [
        {
            "caption": (p.caption or "")[:200],
            "reach": p.reach,
            "likes": p.likes,
            "comments": p.comments,
        }
        for p in rows
    ]


@router.get("/status", response_model=StatusResponse)
def status(db: Session = Depends(get_db)):
    user = get_default_user(db)
    return StatusResponse(
        ready=current_provider() != "none",
        provider=current_provider(),
        niche=user.niche,
        categories=list_categories(),
        languages=list_languages(),
        sources={
            "reddit": {"available": True, "note": "always free"},
            "x": {"available": _x_available(), "note": "free tier with limits" if _x_available() else "needs X_BEARER_TOKEN"},
            "instagram": {"available": False, "note": "requires Meta Developer App"},
        },
    )


@router.post("/start", response_model=StartResponse)
def start(body: StartRequest, db: Session = Depends(get_db)):
    user = get_default_user(db)
    if body.niche:
        user.niche = body.niche
        db.commit()

    if body.count < 1 or body.count > 10:
        raise HTTPException(400, "count must be 1..10")
    if current_provider() == "none":
        raise HTTPException(500, "AI provider not configured. Set GEMINI_API_KEY in backend/.env")

    sources = _fetch_trends(body.category, db)

    trends_for_prompt = {
        "reddit_top_posts": (sources.get("reddit") or {}).get("posts", [])[:18],
        "x_top_tweets": (sources.get("x") or {}).get("top_tweets", [])[:10],
    }

    try:
        items = ai.generate_ideas(
            niche=user.niche,
            category=body.category,
            language=body.language,
            vibe=body.vibe,
            length="30s reel",
            platform=body.platform,
            count=body.count,
            trends=trends_for_prompt,
            top_posts=_top_posts(db, user.id),
        )
    except RateLimitError as e:
        raise HTTPException(429, str(e))

    saved: list[Idea] = []
    for it in items:
        row = Idea(
            user_id=user.id,
            title=str(it.get("title", "Untitled"))[:255],
            hook=str(it.get("hook", "")),
            script_outline=str(it.get("script_outline", "")),
            hashtags=it.get("hashtags", []) or [],
            suggested_time=str(it.get("suggested_time", "")),
            platform=body.platform,
            virality_score=float(it.get("virality_score", 0.0) or 0.0),
            vibe=f"{body.vibe} | {body.category} | {body.language}",
        )
        db.add(row)
        saved.append(row)
    db.commit()
    for r in saved:
        db.refresh(r)

    return StartResponse(
        niche=user.niche,
        category=body.category,
        language=body.language,
        provider=current_provider(),
        sources=sources,
        ideas=[IdeaOut.model_validate(r) for r in saved],
    )


@router.get("/ideas", response_model=List[IdeaOut])
def list_ideas(db: Session = Depends(get_db)):
    user = get_default_user(db)
    rows = (
        db.query(Idea)
        .filter(Idea.user_id == user.id)
        .order_by(Idea.created_at.desc())
        .limit(50)
        .all()
    )
    return [IdeaOut.model_validate(r) for r in rows]


@router.post("/ideas/{idea_id}/script", response_model=ScriptResponse)
def generate_script(
    idea_id: int,
    body: Optional[ScriptRequest] = None,
    db: Session = Depends(get_db),
):
    user = get_default_user(db)
    row = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == user.id).first()
    if not row:
        raise HTTPException(404, "Idea not found")

    vibe_parts = (row.vibe or "").split("|")
    cat = vibe_parts[1].strip() if len(vibe_parts) > 1 else "general"
    detected_lang = vibe_parts[2].strip() if len(vibe_parts) > 2 else "en"
    language = (body.language if body and body.language else detected_lang) or "en"

    try:
        script = ai.generate_full_script(
            niche=user.niche,
            category=cat,
            language=language,
            title=row.title,
            hook=row.hook,
            outline=row.script_outline,
        )
    except RateLimitError as e:
        raise HTTPException(429, str(e))
    return ScriptResponse(idea_id=row.id, title=row.title, script=script, language=language)


@router.delete("/ideas/{idea_id}")
def delete_idea(idea_id: int, db: Session = Depends(get_db)):
    user = get_default_user(db)
    row = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == user.id).first()
    if not row:
        raise HTTPException(404)
    db.delete(row)
    db.commit()
    return {"ok": True}
