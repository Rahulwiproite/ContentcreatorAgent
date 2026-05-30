from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import SocialAccount, User
from ..schemas import ConnectedAccount
from ..security import encrypt_token, get_current_user
from ..services import instagram as ig

settings = get_settings()
router = APIRouter(prefix="/social", tags=["social"])


META_SCOPES = ",".join(
    [
        "instagram_basic",
        "instagram_manage_insights",
        "pages_show_list",
        "pages_read_engagement",
        "business_management",
    ]
)


@router.get("/instagram/connect")
def instagram_connect_url(user: User = Depends(get_current_user)):
    if not settings.META_APP_ID:
        raise HTTPException(500, "META_APP_ID not configured on the server")
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_REDIRECT_URI,
        "scope": META_SCOPES,
        "response_type": "code",
        "state": str(user.id),
    }
    return {"url": f"https://www.facebook.com/v21.0/dialog/oauth?{urlencode(params)}"}


@router.get("/instagram/callback")
def instagram_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == int(state)).first()
    if not user:
        raise HTTPException(400, "Invalid state")
    token_resp = ig.exchange_code_for_token(
        settings.META_APP_ID, settings.META_APP_SECRET, settings.META_REDIRECT_URI, code
    )
    access_token = token_resp.get("access_token")
    if not access_token:
        raise HTTPException(400, f"Token exchange failed: {token_resp}")
    ig_info = ig.get_ig_business_account(access_token)
    if not ig_info:
        raise HTTPException(
            400,
            "No Instagram Business account linked to any Facebook Page. "
            "Convert your IG to a Business/Creator account and link a Page.",
        )

    existing = (
        db.query(SocialAccount)
        .filter(SocialAccount.user_id == user.id, SocialAccount.platform == "instagram")
        .first()
    )
    expires = None
    if token_resp.get("expires_in"):
        expires = datetime.utcnow() + timedelta(seconds=int(token_resp["expires_in"]))
    payload = dict(
        platform="instagram",
        platform_user_id=ig_info["ig_user_id"],
        handle=ig_info["username"],
        access_token_enc=encrypt_token(ig_info["page_access_token"]),
        extra={
            "page_id": ig_info["page_id"],
            "followers_count": ig_info["followers_count"],
            "media_count": ig_info["media_count"],
        },
        expires_at=expires,
    )
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
    else:
        db.add(SocialAccount(user_id=user.id, **payload))
    db.commit()
    return RedirectResponse(url=f"{settings.FRONTEND_ORIGIN}/settings?connected=instagram")


@router.get("/accounts", response_model=list[ConnectedAccount])
def list_accounts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(SocialAccount).filter(SocialAccount.user_id == user.id).all()
    return [ConnectedAccount(platform=r.platform, handle=r.handle, connected_at=r.created_at) for r in rows]


@router.delete("/{platform}")
def disconnect(platform: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(SocialAccount)
        .filter(SocialAccount.user_id == user.id, SocialAccount.platform == platform)
        .all()
    )
    for r in rows:
        db.delete(r)
    db.commit()
    return {"ok": True}
