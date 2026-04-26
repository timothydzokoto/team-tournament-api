from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.schemas.user import UserRegister, UserResponse, UserLogin, TokenPair, RefreshRequest
from app.crud.user import user_crud
from app.crud.refresh_token import refresh_token_crud
from app.utils.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    generate_refresh_token,
    hash_token,
    get_current_active_user,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def _issue_token_pair(db: Session, user) -> TokenPair:
    """Create and persist a fresh access + refresh token pair for a user."""
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    raw_refresh = generate_refresh_token()
    refresh_token_crud.create(
        db=db,
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return TokenPair(access_token=access_token, refresh_token=raw_refresh)


@router.post("/register", response_model=UserResponse)
def register(user: UserRegister, db: Session = Depends(get_db)):
    """Register a new user (role defaults to coach)"""
    if user_crud.get_by_username(db, username=user.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    if user_crud.get_by_email(db, email=user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return user_crud.register(db=db, user=user)


@router.post("/login", response_model=TokenPair)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and return an access token + refresh token"""
    user = user_crud.authenticate(db, username=user_credentials.username, password=user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return _issue_token_pair(db, user)


@router.post("/refresh", response_model=TokenPair)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair (old token is rotated out)"""
    token_hash = hash_token(request.refresh_token)
    db_token = refresh_token_crud.get_by_hash(db, token_hash=token_hash)

    if not db_token or db_token.is_revoked or db_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Rotate: revoke the used token before issuing a new pair
    refresh_token_crud.revoke(db, token_hash=token_hash)

    user = db_token.user
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return _issue_token_pair(db, user)


@router.post("/logout")
def logout(request: RefreshRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token (client should discard the access token too)"""
    refresh_token_crud.revoke(db, token_hash=hash_token(request.refresh_token))
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: UserResponse = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user
