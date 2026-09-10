import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensure all SQLAlchemy models are registered
from app.scheduler.worker import start_scheduler, stop_scheduler
from app.routers import auth_router, oauth_router, posts_router, views_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

# Application Lifespan (Startup / Shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB tables
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Start Background Scheduler Daemon
    logger.info("Starting background scheduler...")
    start_scheduler()
    
    # 3. Pre-warm AI background removal model in background thread
    import threading
    from app.routers.posts import get_rembg_session
    threading.Thread(target=get_rembg_session, daemon=True).start()
    
    yield
    
    # 3. Stop Background Scheduler on shutdown
    logger.info("Stopping background scheduler...")
    stop_scheduler()

# FastAPI App Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-tenant Social Media Scheduling & Automation Hub for Facebook & LinkedIn",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(posts_router)
app.include_router(views_router)

# Mount Static Files (Uploads, Images, CSS)
import os
from fastapi.staticfiles import StaticFiles

static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
os.makedirs(os.path.join(static_dir, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
