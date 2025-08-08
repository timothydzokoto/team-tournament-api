from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.subteam import SubTeam
from app.schemas.subteam import SubTeamCreate, SubTeamUpdate
from app.cache import cache_get, cache_set, cache_delete, cache_clear_pattern

class SubTeamCRUD:
    def create(self, db: Session, subteam: SubTeamCreate) -> SubTeam:
        """Create a new subteam"""
        db_subteam = SubTeam(**subteam.model_dump())
        db.add(db_subteam)
        db.commit()
        db.refresh(db_subteam)
        
        # Clear cache
        cache_clear_pattern("subteams:*")
        return db_subteam
    
    def get(self, db: Session, subteam_id: int) -> Optional[SubTeam]:
        """Get a subteam by ID with caching"""
        cache_key = f"subteam:{subteam_id}"
        cached = cache_get(cache_key)
        if cached:
            return cached
        
        subteam = db.query(SubTeam).filter(SubTeam.id == subteam_id).first()
        if subteam:
            cache_set(cache_key, subteam, 300)  # Cache for 5 minutes
        return subteam
    
    def get_by_team(self, db: Session, team_id: int) -> List[SubTeam]:
        """Get all subteams for a team"""
        return db.query(SubTeam).filter(SubTeam.team_id == team_id).all()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        team_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[SubTeam]:
        """Get multiple subteams with optional filtering"""
        query = db.query(SubTeam)
        
        if team_id:
            query = query.filter(SubTeam.team_id == team_id)
        
        if search:
            query = query.filter(SubTeam.name.ilike(f"%{search}%"))
        
        return query.offset(skip).limit(limit).all()
    
    def update(self, db: Session, subteam_id: int, subteam_update: SubTeamUpdate) -> Optional[SubTeam]:
        """Update a subteam"""
        db_subteam = self.get(db, subteam_id)
        if not db_subteam:
            return None
        
        update_data = subteam_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_subteam, field, value)
        
        db.commit()
        db.refresh(db_subteam)
        
        # Clear cache
        cache_delete(f"subteam:{subteam_id}")
        cache_clear_pattern("subteams:*")
        
        return db_subteam
    
    def delete(self, db: Session, subteam_id: int) -> bool:
        """Delete a subteam"""
        db_subteam = self.get(db, subteam_id)
        if not db_subteam:
            return False
        
        db.delete(db_subteam)
        db.commit()
        
        # Clear cache
        cache_delete(f"subteam:{subteam_id}")
        cache_clear_pattern("subteams:*")
        
        return True

# Create instance
subteam_crud = SubTeamCRUD() 