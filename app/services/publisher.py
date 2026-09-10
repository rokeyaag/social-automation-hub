from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.post import Post, PostDispatchLog
from app.models.social_account import SocialAccount
from app.core.security import decrypt_token
from app.services.facebook_service import FacebookService
from app.services.linkedin_service import LinkedInService

class PublisherService:
    @classmethod
    def dispatch_post(cls, db: Session, post_id: int) -> Dict[str, Any]:
        """Orchestrates publishing a post to all requested platforms."""
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return {"error": f"Post {post_id} not found."}

        target_platforms: List[str] = [
            p.strip().lower() for p in post.target_platforms.split(",") if p.strip()
        ]

        # Fetch user's connected social accounts
        accounts = db.query(SocialAccount).filter(
            SocialAccount.user_id == post.user_id,
            SocialAccount.platform.in_(target_platforms)
        ).all()

        account_map = {acc.platform: acc for acc in accounts}
        success_count = 0
        failure_count = 0

        for platform in target_platforms:
            acc = account_map.get(platform)
            if not acc:
                # User has not connected this platform
                log = PostDispatchLog(
                    post_id=post.id,
                    platform=platform,
                    status="error",
                    error_message=f"No connected account found for {platform}. Please connect it first."
                )
                db.add(log)
                failure_count += 1
                continue

            decrypted_token = decrypt_token(acc.encrypted_access_token)
            dispatch_result: Dict[str, Any] = {}

            try:
                if platform == "facebook":
                    dispatch_result = FacebookService.publish_post(
                        page_id=acc.platform_account_id,
                        access_token=decrypted_token,
                        content=post.content,
                        media_url=post.media_url
                    )
                elif platform == "linkedin":
                    dispatch_result = LinkedInService.publish_post(
                        author_urn=acc.platform_account_id,
                        access_token=decrypted_token,
                        content=post.content,
                        media_url=post.media_url
                    )
                else:
                    dispatch_result = {
                        "success": False,
                        "error": f"Platform '{platform}' is not supported yet."
                    }
            except Exception as e:
                dispatch_result = {"success": False, "error": str(e)}

            if dispatch_result.get("success"):
                success_count += 1
                log = PostDispatchLog(
                    post_id=post.id,
                    platform=platform,
                    platform_post_id=dispatch_result.get("platform_post_id"),
                    status="success",
                    error_message=None
                )
            else:
                failure_count += 1
                log = PostDispatchLog(
                    post_id=post.id,
                    platform=platform,
                    status="error",
                    error_message=dispatch_result.get("error", "Unknown publishing error")
                )

            db.add(log)

        # Update post overall status
        if success_count > 0:
            post.status = "published"
            post.published_at = datetime.now(timezone.utc)
        elif failure_count > 0:
            post.status = "failed"

        db.commit()
        db.refresh(post)

        return {
            "post_id": post.id,
            "status": post.status,
            "successes": success_count,
            "failures": failure_count
        }
