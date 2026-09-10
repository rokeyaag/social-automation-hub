from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.models.post import Post
from app.models.social_account import SocialAccount
from app.services.auth_service import get_current_user_optional

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter(tags=["Frontend Views"])

@router.get("/", response_class=HTMLResponse)
def root(user = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")

@router.get("/login", response_class=HTMLResponse)
def login_view(request: Request, user = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"user": None})

@router.get("/register", response_class=HTMLResponse)
def register_view(request: Request, user = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request=request, name="auth/register.html", context={"user": None})

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/login")

    # Metrics
    total_posts = db.query(Post).filter(Post.user_id == user.id).count()
    scheduled_posts = db.query(Post).filter(Post.user_id == user.id, Post.status == "scheduled").count()
    published_posts = db.query(Post).filter(Post.user_id == user.id, Post.status == "published").count()
    failed_posts = db.query(Post).filter(Post.user_id == user.id, Post.status == "failed").count()

    recent_posts = db.query(Post).filter(Post.user_id == user.id).order_by(Post.created_at.desc()).limit(5).all()
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == user.id).all()

    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "user": user,
        "total_posts": total_posts,
        "scheduled_posts": scheduled_posts,
        "published_posts": published_posts,
        "failed_posts": failed_posts,
        "recent_posts": recent_posts,
        "accounts": accounts
    })

@router.get("/create-post", response_class=HTMLResponse)
def create_post_view(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/login")

    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == user.id).all()
    return templates.TemplateResponse(request=request, name="create_post.html", context={
        "user": user,
        "accounts": accounts
    })

@router.get("/schedule", response_class=HTMLResponse)
def schedule_view(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/login")

    posts = db.query(Post).filter(Post.user_id == user.id).order_by(Post.created_at.desc()).all()
    return templates.TemplateResponse(request=request, name="schedule.html", context={
        "user": user,
        "posts": posts
    })

@router.get("/accounts", response_class=HTMLResponse)
def accounts_view(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/login")

    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == user.id).all()
    has_fb = any(a.platform == "facebook" for a in accounts)
    has_li = any(a.platform == "linkedin" for a in accounts)

    return templates.TemplateResponse(request=request, name="accounts.html", context={
        "user": user,
        "accounts": accounts,
        "has_facebook": has_fb,
        "has_linkedin": has_li
    })
