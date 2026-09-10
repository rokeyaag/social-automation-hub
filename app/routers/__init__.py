from app.routers.auth import router as auth_router
from app.routers.oauth import router as oauth_router
from app.routers.posts import router as posts_router
from app.routers.views import router as views_router

__all__ = ["auth_router", "oauth_router", "posts_router", "views_router"]
