from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, JSON
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(120), default="")
    niche = Column(String(255), default="general comedy")
    created_at = Column(DateTime, default=datetime.utcnow)

    socials = relationship("SocialAccount", back_populates="user", cascade="all,delete")
    ideas = relationship("Idea", back_populates="user", cascade="all,delete")


class SocialAccount(Base):
    __tablename__ = "social_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(20), nullable=False)  # instagram | facebook | twitter
    platform_user_id = Column(String(120), default="")
    handle = Column(String(120), default="")
    access_token_enc = Column(Text, nullable=False)
    refresh_token_enc = Column(Text, default="")
    extra = Column(JSON, default=dict)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="socials")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)
    platform_post_id = Column(String(120), nullable=False)
    caption = Column(Text, default="")
    media_type = Column(String(40), default="")
    media_url = Column(Text, default="")
    permalink = Column(Text, default="")
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    plays = Column(Integer, default=0)
    posted_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class Idea(Base):
    __tablename__ = "ideas"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    hook = Column(Text, default="")
    script_outline = Column(Text, default="")
    hashtags = Column(JSON, default=list)
    suggested_time = Column(String(80), default="")
    platform = Column(String(40), default="instagram")
    virality_score = Column(Float, default=0.0)
    vibe = Column(String(80), default="")
    favorite = Column(Boolean, default=False)
    posted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ideas")


class TrendCache(Base):
    __tablename__ = "trend_cache"
    id = Column(Integer, primary_key=True)
    platform = Column(String(20), nullable=False, index=True)
    payload = Column(JSON, default=dict)
    refreshed_at = Column(DateTime, default=datetime.utcnow)
