from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate
from app.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_get_namespace_version,
    cache_bump_namespace_version,
)

class TeamCRUD:
    LIST_NAMESPACE = "teams:list"

    def create(self, db: Session, team: TeamCreate) -> Team:
        """Create a new team"""
        db_team = Team(**team.model_dump())
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
        
        # Invalidate list cache namespace.
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return db_team
    
    def get(self, db: Session, team_id: int, use_cache: bool = True) -> Optional[Team]:
        """Get a team by ID with caching"""
        cache_key = f"team:{team_id}"
        if use_cache:
            cached = cache_get(cache_key)
            if isinstance(cached, dict):
                return Team(**cached)
        
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            cache_set(cache_key, team, 300)  # Cache for 5 minutes
        return team
    
    def get_by_name(self, db: Session, name: str) -> Optional[Team]:
        """Get a team by name"""
        return db.query(Team).filter(Team.name == name).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Team]:
        """Get multiple teams with optional search"""
        version = cache_get_namespace_version(self.LIST_NAMESPACE)
        normalized_search = (search or "").strip().lower()
        cache_key = f"teams:list:v{version}:skip:{skip}:limit:{limit}:search:{normalized_search}"
        cached = cache_get(cache_key)
        if isinstance(cached, list):
            return [Team(**item) for item in cached if isinstance(item, dict)]

        query = db.query(Team)
        
        if search:
            query = query.filter(Team.name.ilike(f"%{search}%"))
        
        teams = query.offset(skip).limit(limit).all()
        cache_set(cache_key, teams, 300)
        return teams
    
    def count_multi(self, db: Session, search: Optional[str] = None) -> int:
        query = db.query(func.count(Team.id))
        if search:
            query = query.filter(Team.name.ilike(f"%{search}%"))
        return query.scalar()

    def update(self, db: Session, team_id: int, team_update: TeamUpdate) -> Optional[Team]:
        """Update a team"""
        db_team = self.get(db, team_id, use_cache=False)
        if not db_team:
            return None
        
        update_data = team_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_team, field, value)
        
        db.commit()
        db.refresh(db_team)
        
        # Clear cache
        cache_delete(f"team:{team_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        
        return db_team
    
    def delete(self, db: Session, team_id: int) -> bool:
        """Delete a team"""
        db_team = self.get(db, team_id, use_cache=False)
        if not db_team:
            return False
        
        db.delete(db_team)
        db.commit()
        
        # Clear cache
        cache_delete(f"team:{team_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        
        return True

# Create instance
team_crud = TeamCRUD() 
