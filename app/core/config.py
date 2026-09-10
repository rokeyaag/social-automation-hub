import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SocialPulse Hub"
    SECRET_KEY: str = "dev-secret-key-change-in-production-abcdef123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # 32-byte URL-safe base64 key for AES-256 Fernet token encryption
    ENCRYPTION_KEY: str = "uD_W0jP3q_9x1vLk7AeM4z6dF2qV8L1n3B7mX0yZ9A="
    
    # Database
    DATABASE_URL: str = "sqlite:///./automation.db"
    
    # Simulation / Demo Mode (Set True to test without live API credentials)
    DEMO_MODE: bool = True
    
    # Meta / Facebook OAuth
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/facebook/callback"
    
    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/linkedin/callback"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
