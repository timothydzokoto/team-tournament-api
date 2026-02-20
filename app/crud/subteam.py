from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.subteam import SubTeam
from app.schemas.subteam import SubTeamCreate, SubTeamUpdate
from app.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_get_namespace_version,
    cache_bump_namespace_version,
)

class SubTeamCRUD:
    LIST_NAMESPACE = "subteams:list"

    def create(self, db: Session, subteam: SubTeamCreate) -> SubTeam:
        """Create a new subteam"""
        db_subteam = SubTeam(**subteam.model_dump())
        db.add(db_subteam)
        db.commit()
        db.refresh(db_subteam)
        
        # Invalidate list cache namespace.
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return db_subteam
    
    def get(self, db: Session, subteam_id: int, use_cache: bool = True) -> Optional[SubTeam]:
        """Get a subteam by ID with caching"""
        cache_key = f"subteam:{subteam_id}"
        if use_cache:
            cached = cache_get(cache_key)
            if isinstance(cached, dict):
                return SubTeam(**cached)
        
        subteam = db.query(SubTeam).filter(SubTeam.id == subteam_id).first()
        if subteam:
            cache_set(cache_key, subteam, 300)  # Cache for 5 minutes
        return subteam
    
    def get_by_team(self, db: Session, team_id: int) -> List[SubTeam]:
        """Get all subteams for a team"""
        version = cache_get_namespace_version(self.LIST_NAMESPACE)
        cache_key = f"subteams:list:v{version}:team:{team_id}"
        cached = cache_get(cache_key)
        if isinstance(cached, list):
            return [SubTeam(**item) for item in cached if isinstance(item, dict)]

        subteams = db.query(SubTeam).filter(SubTeam.team_id == team_id).all()
        cache_set(cache_key, subteams, 300)
        return subteams
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        team_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[SubTeam]:
        """Get multiple subteams with optional filtering"""
        version = cache_get_namespace_version(self.LIST_NAMESPACE)
        normalized_team = team_id if team_id is not None else "all"
        normalized_search = (search or "").strip().lower()
        cache_key = (
            f"subteams:list:v{version}:skip:{skip}:limit:{limit}:"
            f"team:{normalized_team}:search:{normalized_search}"
        )
        cached = cache_get(cache_key)
        if isinstance(cached, list):
            return [SubTeam(**item) for item in cached if isinstance(item, dict)]

        query = db.query(SubTeam)
        
        if team_id:
            query = query.filter(SubTeam.team_id == team_id)
        
        if search:
            query = query.filter(SubTeam.name.ilike(f"%{search}%"))
        
        subteams = query.offset(skip).limit(limit).all()
        cache_set(cache_key, subteams, 300)
        return subteams
    
    def update(self, db: Session, subteam_id: int, subteam_update: SubTeamUpdate) -> Optional[SubTeam]:
        """Update a subteam"""
        db_subteam = self.get(db, subteam_id, use_cache=False)
        if not db_subteam:
            return None
        
        update_data = subteam_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_subteam, field, value)
        
        db.commit()
        db.refresh(db_subteam)
        
        # Clear cache
        cache_delete(f"subteam:{subteam_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        
        return db_subteam
    
    def delete(self, db: Session, subteam_id: int) -> bool:
        """Delete a subteam"""
        db_subteam = self.get(db, subteam_id, use_cache=False)
        if not db_subteam:
            return False
        
        db.delete(db_subteam)
        db.commit()
        
        # Clear cache
        cache_delete(f"subteam:{subteam_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        
        return True

# Create instance
subteam_crud = SubTeamCRUD() 
