from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: Optional[str] = ""
    niche: Optional[str] = "general comedy"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    niche: str

    class Config:
        from_attributes = True


class UpdateProfile(BaseModel):
    display_name: Optional[str] = None
    niche: Optional[str] = None


class IdeaRequest(BaseModel):
    vibe: str = "absurd observational"
    length: str = "30s reel"
    platform: str = "instagram"
    count: int = 5


class IdeaOut(BaseModel):
    id: int
    title: str
    hook: str
    script_outline: str
    hashtags: List[str]
    suggested_time: str
    platform: str
    virality_score: float
    vibe: str
    favorite: bool
    posted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConnectedAccount(BaseModel):
    platform: str
    handle: str
    connected_at: datetime

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
