import requests
import uuid
from typing import Dict, Any, Optional
from app.core.config import settings

class LinkedInService:
    API_BASE = "https://api.linkedin.com"

    @classmethod
    def get_authorization_url(cls, state: str) -> str:
        """Constructs LinkedIn OAuth 2.0 URL."""
        if settings.DEMO_MODE or not settings.LINKEDIN_CLIENT_ID:
            return f"/api/v1/oauth/linkedin/simulate-callback?state={state}"

        scope = "openid profile email w_member_social"
        return (
            f"https://www.linkedin.com/oauth/v2/authorization?"
            f"response_type=code&"
            f"client_id={settings.LINKEDIN_CLIENT_ID}&"
            f"redirect_uri={settings.LINKEDIN_REDIRECT_URI}&"
            f"state={state}&"
            f"scope={scope}"
        )

    @classmethod
    def exchange_code_for_token(cls, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for LinkedIn access token and fetches profile URN."""
        if settings.DEMO_MODE or not settings.LINKEDIN_CLIENT_ID:
            return {
                "platform_account_id": f"urn:li:person:demo_{uuid.uuid4().hex[:8]}",
                "account_name": "Demo Professional Profile",
                "account_type": "profile",
                "access_token": f"sim_li_token_{uuid.uuid4().hex}"
            }

        # 1. Exchange code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET
        }
        res = requests.post(token_url, data=data, timeout=15)
        res.raise_for_status()
        token_info = res.json()
        access_token = token_info.get("access_token")

        # 2. Get User Profile Info (OpenID userinfo)
        userinfo_url = f"{cls.API_BASE}/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_res = requests.get(userinfo_url, headers=headers, timeout=15)
        user_res.raise_for_status()
        profile_data = user_res.json()

        person_sub = profile_data.get("sub")
        account_name = profile_data.get("name", "LinkedIn Member")

        return {
            "platform_account_id": f"urn:li:person:{person_sub}",
            "account_name": account_name,
            "account_type": "profile",
            "access_token": access_token
        }

    @classmethod
    def publish_post(cls, author_urn: str, access_token: str, content: str, media_url: Optional[str] = None) -> Dict[str, Any]:
        """Publishes a text or link post to LinkedIn using the UGC Posts API."""
        if settings.DEMO_MODE or access_token.startswith("sim_"):
            return {
                "success": True,
                "platform_post_id": f"urn:li:share:sim_{uuid.uuid4().hex[:12]}",
                "message": "Simulated post published successfully to LinkedIn."
            }

        url = f"{cls.API_BASE}/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        if media_url:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "originalUrl": media_url
            }]

        response = requests.post(url, headers=headers, json=payload, timeout=20)
        data = response.json()

        if response.status_code not in (200, 201):
            error_msg = data.get("message", "LinkedIn API publish error")
            return {"success": False, "error": error_msg}

        return {
            "success": True,
            "platform_post_id": data.get("id"),
            "message": "Post successfully published to LinkedIn."
        }
