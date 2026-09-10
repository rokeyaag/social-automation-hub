from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    media_url = Column(String(500), nullable=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    status = Column(String(50), default="scheduled", index=True)  # draft, scheduled, publishing, published, failed
    target_platforms = Column(String(255), default="facebook,linkedin")  # comma-separated or json string
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="posts")
    dispatch_logs = relationship("PostDispatchLog", back_populates="post", cascade="all, delete-orphan")


class PostDispatchLog(Base):
    __tablename__ = "post_dispatch_logs"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # 'facebook' or 'linkedin'
    platform_post_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)  # 'success' or 'error'
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="dispatch_logs")
