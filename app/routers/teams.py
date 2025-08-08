from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamList
from app.crud.team import team_crud
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("/", response_model=TeamResponse)
def create_team(
    team: TeamCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new team"""
    # Check if team name already exists
    existing_team = team_crud.get_by_name(db, name=team.name)
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists"
        )
    
    return team_crud.create(db=db, team=team)

@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a team by ID"""
    team = team_crud.get(db, team_id=team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team

@router.get("/", response_model=List[TeamResponse])
def get_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all teams with optional search"""
    teams = team_crud.get_multi(db=db, skip=skip, limit=limit, search=search)
    return teams

@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_update: TeamUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a team"""
    team = team_crud.update(db=db, team_id=team_id, team_update=team_update)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team

@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a team"""
    success = team_crud.delete(db=db, team_id=team_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return {"message": "Team deleted successfully"} 