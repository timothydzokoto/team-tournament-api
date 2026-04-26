from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.user import User
from app.schemas.user import UserCreate, UserRegister, UserUpdate
from app.utils.auth import get_password_hash

class UserCRUD:
    def create(self, db: Session, user: UserCreate) -> User:
        """Create a new user with hashed password (admin path — role honoured)."""
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            role=user.role.value if hasattr(user.role, "value") else user.role,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def register(self, db: Session, user: UserRegister) -> User:
        """Create a user from public registration — role is always coach."""
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            role="coach",
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get(self, db: Session, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get a user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get a user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        from app.utils.auth import verify_password
        
        user = self.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get multiple users"""
        return db.query(User).offset(skip).limit(limit).all()
    
    def update(self, db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update a user"""
        db_user = self.get(db, user_id)
        if not db_user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Handle password hashing
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def delete(self, db: Session, user_id: int) -> bool:
        """Delete a user"""
        db_user = self.get(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        return True

# Create instance
user_crud = UserCRUD() 