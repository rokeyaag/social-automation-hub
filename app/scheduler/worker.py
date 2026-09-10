import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.models.post import Post
from app.services.publisher import PublisherService

logger = logging.getLogger("scheduler")
scheduler = BackgroundScheduler()

def check_and_publish_pending_posts():
    """Background job that finds scheduled posts that are due and dispatches them."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # Find posts that are due
        due_posts = db.query(Post).filter(
            Post.status == "scheduled",
            Post.scheduled_at <= now
        ).all()

        if due_posts:
            logger.info(f"Scheduler found {len(due_posts)} due post(s) to publish.")

        for post in due_posts:
            logger.info(f"Triggering dispatch for post ID: {post.id}")
            post.status = "publishing"
            db.commit()

            PublisherService.dispatch_post(db, post.id)

    except Exception as e:
        logger.error(f"Error during scheduler check: {e}", exc_info=True)
    finally:
        db.close()

def start_scheduler():
    """Starts the background scheduler daemon."""
    if not scheduler.running:
        scheduler.add_job(
            check_and_publish_pending_posts,
            "interval",
            seconds=15,
            id="publish_due_posts_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler worker started (interval: 15s).")

def stop_scheduler():
    """Stops the background scheduler cleanly."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler worker stopped.")
