from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from src.api.core.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password for storage."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return pwd_context.verify(password, password_hash)


# PUBLIC_INTERFACE
def create_access_token(subject: str) -> str:
    """Create a signed JWT access token for the given subject (user id)."""
    settings = get_settings()
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET must be set in environment variables")

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# PUBLIC_INTERFACE
def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET must be set in environment variables")
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
