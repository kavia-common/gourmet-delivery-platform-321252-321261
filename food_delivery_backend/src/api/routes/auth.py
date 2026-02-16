from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.security import create_access_token, hash_password, verify_password
from src.api.db.models import User
from src.api.db.session import get_db
from src.api.deps import get_current_user
from src.api.schemas import LoginRequest, SignupRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=201,
    summary="Sign up",
    description="Create a new user account and return an access token.",
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description="Authenticate with email/password and return an access token.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user",
    description="Return the authenticated user profile.",
)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=current_user.id, email=current_user.email)
