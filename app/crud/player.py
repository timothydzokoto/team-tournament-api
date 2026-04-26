from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerFaceMatch
from app.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_get_namespace_version,
    cache_bump_namespace_version,
)
from app.utils.face_recognition import (
    encode_face_from_bytes,
    find_best_match,
    save_face_encoding,
    load_face_encoding,
)
import numpy as np

class PlayerCRUD:
    LIST_NAMESPACE = "players:list"

    def create(self, db: Session, player: PlayerCreate) -> Player:
        """Create a new player"""
        db_player = Player(**player.model_dump())
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        
        # Invalidate list cache namespace.
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return db_player
    
    def get(self, db: Session, player_id: int, use_cache: bool = True) -> Optional[Player]:
        """Get a player by ID with caching"""
        cache_key = f"player:{player_id}"
        if use_cache:
            cached = cache_get(cache_key)
            if isinstance(cached, dict):
                return Player(**cached)
        
        player = db.query(Player).filter(Player.id == player_id).first()
        if player:
            cache_set(cache_key, player, 300)  # Cache for 5 minutes
        return player
    
    def get_by_email(self, db: Session, email: str) -> Optional[Player]:
        """Get a player by email"""
        return db.query(Player).filter(Player.email == email).first()
    
    def get_by_subteam(self, db: Session, subteam_id: int, skip: int = 0, limit: int = 100) -> List[Player]:
        """Get all players for a subteam"""
        version = cache_get_namespace_version(self.LIST_NAMESPACE)
        cache_key = f"players:list:v{version}:skip:{skip}:limit:{limit}:subteam:{subteam_id}"
        cached = cache_get(cache_key)
        if isinstance(cached, list):
            return [Player(**item) for item in cached if isinstance(item, dict)]

        players = db.query(Player).filter(Player.subteam_id == subteam_id).offset(skip).limit(limit).all()
        cache_set(cache_key, players, 300)
        return players
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        subteam_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Player]:
        """Get multiple players with optional filtering"""
        version = cache_get_namespace_version(self.LIST_NAMESPACE)
        normalized_search = (search or "").strip().lower()
        normalized_subteam = subteam_id if subteam_id is not None else "all"
        cache_key = (
            f"players:list:v{version}:skip:{skip}:limit:{limit}:"
            f"subteam:{normalized_subteam}:search:{normalized_search}"
        )
        cached = cache_get(cache_key)
        if isinstance(cached, list):
            return [Player(**item) for item in cached if isinstance(item, dict)]

        query = db.query(Player)
        
        if subteam_id:
            query = query.filter(Player.subteam_id == subteam_id)
        
        if search:
            query = query.filter(
                (Player.first_name.ilike(f"%{search}%")) |
                (Player.last_name.ilike(f"%{search}%")) |
                (Player.email.ilike(f"%{search}%"))
            )
        
        players = query.offset(skip).limit(limit).all()
        cache_set(cache_key, players, 300)
        return players
    
    def count_multi(
        self,
        db: Session,
        subteam_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> int:
        query = db.query(func.count(Player.id))
        if subteam_id:
            query = query.filter(Player.subteam_id == subteam_id)
        if search:
            query = query.filter(
                (Player.first_name.ilike(f"%{search}%")) |
                (Player.last_name.ilike(f"%{search}%")) |
                (Player.email.ilike(f"%{search}%"))
            )
        return query.scalar()

    def update(self, db: Session, player_id: int, player_update: PlayerUpdate) -> Optional[Player]:
        """Update a player"""
        db_player = self.get(db, player_id, use_cache=False)
        if not db_player:
            return None
        
        update_data = player_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_player, field, value)
        
        db.commit()
        db.refresh(db_player)
        
        # Clear cache
        cache_delete(f"player:{player_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        
        return db_player
    
    def delete(self, db: Session, player_id: int) -> bool:
        """Delete a player"""
        db_player = self.get(db, player_id, use_cache=False)
        if not db_player:
            return False
        
        db.delete(db_player)
        db.commit()
        
        # Clear cache
        cache_delete(f"player:{player_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        
        return True
    
    def find_player_by_face(self, db: Session, face_image_bytes: bytes) -> Optional[PlayerFaceMatch]:
        """Find a player by face recognition"""
        # Encode the unknown face
        unknown_encoding = encode_face_from_bytes(face_image_bytes)

        # Get all players with face encodings
        players_with_faces = db.query(Player).filter(Player.face_encoding.isnot(None)).all()

        if not players_with_faces:
            return None

        # Prepare known encodings
        known_encodings = []
        for player in players_with_faces:
            encoding = load_face_encoding(player.face_encoding)
            if encoding is not None:
                known_encodings.append((player.id, encoding))

        # Find best match
        match_result = find_best_match(unknown_encoding, known_encodings)
        if match_result is None:
            return None

        player_id, confidence = match_result
        player = self.get(db, player_id, use_cache=False)

        if player:
            return PlayerFaceMatch(
                player_id=player.id,
                player_name=player.full_name,
                confidence=confidence,
                face_image_url=player.face_image_url
            )

        return None

    def update_face_encoding(self, db: Session, player_id: int, face_image_bytes: bytes, face_image_url: str) -> Optional[Player]:
        """Update player's face encoding"""
        db_player = self.get(db, player_id, use_cache=False)
        if not db_player:
            return None

        # Encode the face
        encoding = encode_face_from_bytes(face_image_bytes)

        # Save encoding as JSON string
        encoding_str = save_face_encoding(encoding)

        # Update player
        db_player.face_encoding = encoding_str
        db_player.face_image_url = face_image_url
        db.commit()
        db.refresh(db_player)

        # Clear cache
        cache_delete(f"player:{player_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)

        return db_player

# Create instance
player_crud = PlayerCRUD() 
