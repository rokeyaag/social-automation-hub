import requests
import uuid
from typing import Dict, Any, Optional
from app.core.config import settings

class FacebookService:
    GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

    @classmethod
    def get_authorization_url(cls, state: str) -> str:
        """Constructs Facebook OAuth 2.0 URL."""
        if settings.DEMO_MODE or not settings.META_APP_ID:
            # In demo mode, redirect to our simulation callback directly
            return f"/api/v1/oauth/facebook/simulate-callback?state={state}"
        
        scope = "pages_show_list,pages_read_engagement,pages_manage_posts"
        return (
            f"https://www.facebook.com/v19.0/dialog/oauth?"
            f"client_id={settings.META_APP_ID}&"
            f"redirect_uri={settings.META_REDIRECT_URI}&"
            f"state={state}&"
            f"scope={scope}"
        )

    @classmethod
    def exchange_code_for_token(cls, code: str) -> Dict[str, Any]:
        """Exchanges OAuth code for long-lived access token and fetches primary managed page."""
        if settings.DEMO_MODE or not settings.META_APP_ID:
            return {
                "platform_account_id": f"fb_page_{uuid.uuid4().hex[:8]}",
                "account_name": "Demo Business Page",
                "account_type": "page",
                "access_token": f"sim_fb_token_{uuid.uuid4().hex}"
            }

        # 1. Exchange code for user access token
        token_url = f"{cls.GRAPH_API_BASE}/oauth/access_token"
        params = {
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "redirect_uri": settings.META_REDIRECT_URI,
            "code": code
        }
        res = requests.get(token_url, params=params, timeout=15)
        res.raise_for_status()
        user_access_token = res.json().get("access_token")

        # 2. Get User's Facebook Pages
        pages_url = f"{cls.GRAPH_API_BASE}/me/accounts"
        pages_res = requests.get(pages_url, params={"access_token": user_access_token}, timeout=15)
        pages_res.raise_for_status()
        data = pages_res.json().get("data", [])

        if not data:
            raise ValueError("No Facebook Pages found associated with this account.")

        primary_page = data[0]
        return {
            "platform_account_id": primary_page["id"],
            "account_name": primary_page.get("name", "Facebook Page"),
            "account_type": "page",
            "access_token": primary_page["access_token"]
        }

    @classmethod
    def verify_page_token(cls, page_id: str, access_token: str) -> Dict[str, Any]:
        """Verifies a Facebook Page ID and Page Access Token with Meta Graph API."""
        if access_token.startswith("sim_"):
            return {
                "valid": True,
                "page_id": page_id or "fb_page_demo",
                "page_name": "Demo Business Page",
                "is_simulation": True
            }

        url = f"{cls.GRAPH_API_BASE}/{page_id.strip()}"
        params = {"fields": "id,name,category,link", "access_token": access_token.strip()}
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            if response.status_code != 200:
                err = data.get("error", {}).get("message", "Invalid Page ID or Access Token")
                return {"valid": False, "error": err}

            return {
                "valid": True,
                "page_id": str(data.get("id")),
                "page_name": data.get("name", "Facebook Page"),
                "is_simulation": False
            }
        except Exception as e:
            return {"valid": False, "error": f"Failed to connect to Meta API: {str(e)}"}

    @classmethod
    def publish_post(cls, page_id: str, access_token: str, content: str, media_url: Optional[str] = None) -> Dict[str, Any]:
        """Publishes post to Facebook Page feed with local photo upload support."""
        import os

        # Check for simulated demo token
        if access_token.startswith("sim_") or str(page_id).startswith("fb_page_"):
            return {
                "success": True,
                "platform_post_id": f"fb_sim_{page_id}_{uuid.uuid4().hex[:10]}",
                "message": "Simulated post published successfully to Facebook Page (Demo Mode)."
            }

        # Resolve local photo path if media_url is provided
        local_path = None
        if media_url:
            if media_url.startswith("/static/"):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                clean_rel = media_url.lstrip("/")
                candidate = os.path.join(base_dir, clean_rel)
                if os.path.exists(candidate):
                    local_path = candidate
            elif os.path.isfile(media_url):
                local_path = media_url

        try:
            if local_path and os.path.exists(local_path):
                # Real binary photo upload to Facebook Page Photos endpoint
                url = f"{cls.GRAPH_API_BASE}/{page_id}/photos"
                with open(local_path, "rb") as img_file:
                    files = {"source": img_file}
                    data = {"caption": content, "access_token": access_token}
                    response = requests.post(url, data=data, files=files, timeout=45)
            else:
                # Text post or public URL link
                url = f"{cls.GRAPH_API_BASE}/{page_id}/feed"
                payload: Dict[str, Any] = {"message": content, "access_token": access_token}
                if media_url and media_url.startswith("http"):
                    payload["link"] = media_url
                response = requests.post(url, data=payload, timeout=25)

            data = response.json()
            if response.status_code != 200:
                error_msg = data.get("error", {}).get("message", "Facebook API error")
                return {"success": False, "error": error_msg}

            post_id = data.get("post_id") or data.get("id")
            return {
                "success": True,
                "platform_post_id": post_id,
                "message": "Post successfully published to real Facebook Page!"
            }
        except Exception as e:
            return {"success": False, "error": f"Network or Meta API error: {str(e)}"}
