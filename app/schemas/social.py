from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SocialAccountOut(BaseModel):
    id: int
    platform: str
    platform_account_id: str
    account_name: str
    account_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConnectSimulationRequest(BaseModel):
    platform: str  # 'facebook' or 'linkedin'
    account_name: Optional[str] = None
    account_type: Optional[str] = "page"

class FacebookManualConnectRequest(BaseModel):
    page_id: str
    access_token: str
    page_name: Optional[str] = None

