from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.models.refresh_token import RefreshToken


class RefreshTokenCRUD:

    def create(self, db: Session, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        db_token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    def get_by_hash(self, db: Session, token_hash: str) -> Optional[RefreshToken]:
        return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    def revoke(self, db: Session, token_hash: str) -> bool:
        db_token = self.get_by_hash(db, token_hash)
        if not db_token:
            return False
        db_token.is_revoked = True
        db.commit()
        return True

    def revoke_all_for_user(self, db: Session, user_id: int) -> None:
        """Revoke every active token for a user (e.g. password change, security event)."""
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
        ).update({"is_revoked": True})
        db.commit()

    def cleanup_expired(self, db: Session) -> int:
        """Delete tokens that are both expired and revoked. Returns count deleted."""
        deleted = (
            db.query(RefreshToken)
            .filter(RefreshToken.expires_at < datetime.utcnow())
            .delete()
        )
        db.commit()
        return deleted


refresh_token_crud = RefreshTokenCRUD()
