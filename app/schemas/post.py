from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class PostDispatchLogOut(BaseModel):
    id: int
    platform: str
    platform_post_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    executed_at: datetime

    class Config:
        from_attributes = True

class PostBase(BaseModel):
    content: str
    media_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    target_platforms: Optional[str] = "facebook,linkedin"

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content: Optional[str] = None
    media_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    target_platforms: Optional[str] = None
    status: Optional[str] = None

class PostOut(PostBase):
    id: int
    user_id: int
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
    dispatch_logs: List[PostDispatchLogOut] = []

    class Config:
        from_attributes = True
