from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.security import decode_access_token
from src.api.db.models import User
from src.api.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# PUBLIC_INTERFACE
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """Return the current authenticated user based on JWT bearer token."""
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise ValueError("Missing subject")
        user_id = int(sub)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user
