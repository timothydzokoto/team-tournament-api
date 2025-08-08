from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.crud.user import user_crud
from app.utils.auth import get_current_superuser

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Create a new user (admin only)"""
    # Check if username already exists
    existing_user = user_crud.get_by_username(db, username=user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_user = user_crud.get_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    return user_crud.create(db=db, user=user)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Get a user by ID (admin only)"""
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Get all users (admin only)"""
    users = user_crud.get_multi(db=db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Update a user (admin only)"""
    # Prevent self-deletion
    if user_id == current_user.id and user_update.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = user_crud.update(db=db, user_id=user_id, user_update=user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Delete a user (admin only)"""
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = user_crud.delete(db=db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"} 