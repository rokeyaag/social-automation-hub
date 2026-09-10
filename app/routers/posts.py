from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.post import Post
from app.schemas.post import PostCreate, PostOut, PostUpdate
from app.services.auth_service import get_current_user
from app.services.publisher import PublisherService
import uuid
import os
import shutil
import base64
from fastapi import File, UploadFile
from pydantic import BaseModel
import logging

logger = logging.getLogger("posts")

_rembg_session = None

def get_rembg_session():
    """Initializes and returns cached rembg session using high-speed u2net model."""
    global _rembg_session
    if _rembg_session is None:
        try:
            from rembg import new_session
            _rembg_session = new_session("u2net")
            logger.info("rembg session initialized successfully with u2net model.")
        except Exception as e:
            logger.warning(f"Failed to load u2net model, trying u2netp: {e}")
            try:
                from rembg import new_session
                _rembg_session = new_session("u2netp")
                logger.info("rembg session initialized successfully with u2netp model.")
            except Exception as e2:
                logger.error(f"Failed to initialize any rembg model: {e2}")
    return _rembg_session

router = APIRouter(prefix="/api/v1/posts", tags=["Posts & Scheduling"])

class Base64UploadRequest(BaseModel):
    image_data: str
    filename: Optional[str] = None

@router.post("/upload-media")
async def upload_media(
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user)
):
    """Uploads an image file to the server and returns its public URL."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "png"
    if ext not in ["jpg", "jpeg", "png", "webp", "gif"]:
        ext = "png"
        
    unique_filename = f"user_{current_user.id}_{uuid.uuid4().hex[:10]}.{ext}"
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    media_url = f"/static/uploads/{unique_filename}"
    return {"url": media_url, "filename": unique_filename}

@router.post("/upload-base64")
async def upload_base64(
    payload: Base64UploadRequest,
    current_user: User = Depends(get_current_user)
):
    """Saves canvas base64 image data to the server static uploads folder."""
    raw_data = payload.image_data
    if "," in raw_data:
        raw_data = raw_data.split(",")[1]
    
    unique_filename = f"edited_{current_user.id}_{uuid.uuid4().hex[:10]}.png"
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(base64.b64decode(raw_data))

    media_url = f"/static/uploads/{unique_filename}"
    return {"url": media_url, "filename": unique_filename}

@router.post("/remove-bg")
async def remove_background(
    payload: Base64UploadRequest,
    current_user: User = Depends(get_current_user)
):
    """Removes image background with AI (u2net model) in <0.5 seconds."""
    raw_data = payload.image_data
    if "," in raw_data:
        raw_data = raw_data.split(",")[1]
    
    input_bytes = base64.b64decode(raw_data)
    
    # 1. High accuracy AI background removal using u2net session
    session = get_rembg_session()
    if session:
        try:
            from rembg import remove
            output_bytes = remove(input_bytes, session=session)
            output_b64 = base64.b64encode(output_bytes).decode("utf-8")
            return {"image_data": f"data:image/png;base64,{output_b64}", "method": "ai_u2net"}
        except Exception as e:
            logger.exception("AI rembg failed, falling back to smart key: %s", e)

    # 2. Smart fallback if rembg fails
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(input_bytes)).convert("RGBA")
        datas = img.getdata()
        
        w, h = img.size
        tl = img.getpixel((0, 0))[:3]
        
        new_data = []
        for item in datas:
            dist = sum(abs(item[i] - tl[i]) for i in range(3))
            if dist < 65:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
                
        img.putdata(new_data)
        out_buf = io.BytesIO()
        img.save(out_buf, format="PNG")
        output_b64 = base64.b64encode(out_buf.getvalue()).decode("utf-8")
        return {"image_data": f"data:image/png;base64,{output_b64}", "method": "fast_smart_key"}
    except Exception as e:
        logger.error(f"Fallback bg removal error: {e}")
        raise HTTPException(status_code=500, detail="Background removal failed.")

@router.post("", response_model=PostOut)
def create_post(
    post_in: PostCreate,
    publish_now: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a post. If publish_now=True or scheduled_at is None, dispatches immediately."""
    status_val = "scheduled"
    sched_at = post_in.scheduled_at

    if publish_now or not sched_at:
        sched_at = datetime.now(timezone.utc)
        status_val = "publishing"

    new_post = Post(
        user_id=current_user.id,
        content=post_in.content,
        media_url=post_in.media_url,
        scheduled_at=sched_at,
        status=status_val,
        target_platforms=post_in.target_platforms or "facebook,linkedin"
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    if publish_now or not post_in.scheduled_at:
        PublisherService.dispatch_post(db, new_post.id)
        db.refresh(new_post)

    return new_post

@router.get("", response_model=List[PostOut])
def list_posts(
    status_filter: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists posts created by current user."""
    query = db.query(Post).filter(Post.user_id == current_user.id)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    return query.order_by(Post.created_at.desc()).limit(limit).all()

@router.get("/{post_id}", response_model=PostOut)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return post

@router.post("/{post_id}/publish-now", response_model=PostOut)
def publish_now(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Forces immediate publishing of a scheduled or draft post."""
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    PublisherService.dispatch_post(db, post.id)
    db.refresh(post)
    return post

@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully."}
