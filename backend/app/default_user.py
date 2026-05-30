"""No-auth mode: a single default user is auto-created and used implicitly."""
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import User

DEFAULT_EMAIL = "agent@local"
DEFAULT_NICHE = "creator focused on relatable Indian audience content"


def ensure_default_user() -> int:
    db: Session = SessionLocal()
    try:
        u = db.query(User).filter(User.email == DEFAULT_EMAIL).first()
        if not u:
            u = User(
                email=DEFAULT_EMAIL,
                password_hash="!noauth!",
                display_name="Agent",
                niche=DEFAULT_NICHE,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
        return u.id
    finally:
        db.close()


def get_default_user(db: Session) -> User:
    u = db.query(User).filter(User.email == DEFAULT_EMAIL).first()
    if not u:
        uid = ensure_default_user()
        u = db.query(User).filter(User.id == uid).first()
    return u
