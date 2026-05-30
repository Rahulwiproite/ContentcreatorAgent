from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Idea, Post, TrendCache, User
from ..schemas import IdeaOut, IdeaRequest
from ..security import get_current_user
from ..services import ai

router = APIRouter(prefix="/ideas", tags=["ideas"])


def _latest_trends(db: Session) -> dict:
    out = {}
    for row in db.query(TrendCache).order_by(TrendCache.refreshed_at.desc()).limit(5):
        if row.platform not in out:
            out[row.platform] = row.payload
    return out


def _top_posts(db: Session, user_id: int, n: int = 10) -> list[dict]:
    rows = (
        db.query(Post)
        .filter(Post.user_id == user_id, Post.platform == "instagram")
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
            "media_type": p.media_type,
        }
        for p in rows
    ]


@router.post("/generate", response_model=List[IdeaOut])
def generate(
    body: IdeaRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.count < 1 or body.count > 10:
        raise HTTPException(400, "count must be 1..10")
    ideas = ai.generate_ideas(
        niche=user.niche,
        vibe=body.vibe,
        length=body.length,
        platform=body.platform,
        count=body.count,
        trends=_latest_trends(db),
        top_posts=_top_posts(db, user.id),
    )
    saved: list[Idea] = []
    for it in ideas:
        row = Idea(
            user_id=user.id,
            title=str(it.get("title", "Untitled"))[:255],
            hook=str(it.get("hook", "")),
            script_outline=str(it.get("script_outline", "")),
            hashtags=it.get("hashtags", []) or [],
            suggested_time=str(it.get("suggested_time", "")),
            platform=body.platform,
            virality_score=float(it.get("virality_score", 0.0) or 0.0),
            vibe=body.vibe,
        )
        db.add(row)
        saved.append(row)
    db.commit()
    for r in saved:
        db.refresh(r)
    return [IdeaOut.model_validate(r) for r in saved]


@router.get("/library", response_model=List[IdeaOut])
def library(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Idea)
        .filter(Idea.user_id == user.id)
        .order_by(Idea.created_at.desc())
        .limit(200)
        .all()
    )
    return [IdeaOut.model_validate(r) for r in rows]


@router.post("/{idea_id}/favorite", response_model=IdeaOut)
def toggle_favorite(idea_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == user.id).first()
    if not row:
        raise HTTPException(404, "Not found")
    row.favorite = not row.favorite
    db.commit()
    db.refresh(row)
    return IdeaOut.model_validate(row)


@router.post("/{idea_id}/posted", response_model=IdeaOut)
def mark_posted(idea_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == user.id).first()
    if not row:
        raise HTTPException(404, "Not found")
    row.posted = True
    db.commit()
    db.refresh(row)
    return IdeaOut.model_validate(row)


@router.delete("/{idea_id}")
def delete(idea_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == user.id).first()
    if not row:
        raise HTTPException(404, "Not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
