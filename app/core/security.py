from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
import bcrypt
from jose import jwt, JWTError
from cryptography.fernet import Fernet
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")

# JWT Authentication
def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# Social Access Token Encryption (Fernet AES-256)
try:
    _fernet = Fernet(settings.ENCRYPTION_KEY.encode())
except Exception:
    # Fallback to generate a deterministic valid key if invalid in dev
    _fernet = Fernet(Fernet.generate_key())

def encrypt_token(plain_token: str) -> str:
    if not plain_token:
        return ""
    return _fernet.encrypt(plain_token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    try:
        return _fernet.decrypt(encrypted_token.encode()).decode()
    except Exception:
        return encrypted_token
