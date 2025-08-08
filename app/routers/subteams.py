from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.subteam import SubTeamCreate, SubTeamUpdate, SubTeamResponse
from app.crud.subteam import subteam_crud
from app.crud.team import team_crud
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/subteams", tags=["subteams"])

@router.post("/", response_model=SubTeamResponse)
def create_subteam(
    subteam: SubTeamCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new subteam"""
    # Check if parent team exists
    parent_team = team_crud.get(db, team_id=subteam.team_id)
    if not parent_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent team not found"
        )
    
    return subteam_crud.create(db=db, subteam=subteam)

@router.get("/{subteam_id}", response_model=SubTeamResponse)
def get_subteam(
    subteam_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a subteam by ID"""
    subteam = subteam_crud.get(db, subteam_id=subteam_id)
    if not subteam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subteam not found"
        )
    return subteam

@router.get("/", response_model=List[SubTeamResponse])
def get_subteams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all subteams with optional filtering"""
    subteams = subteam_crud.get_multi(
        db=db, 
        skip=skip, 
        limit=limit, 
        team_id=team_id,
        search=search
    )
    return subteams

@router.get("/team/{team_id}", response_model=List[SubTeamResponse])
def get_subteams_by_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all subteams for a specific team"""
    # Check if team exists
    team = team_crud.get(db, team_id=team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    subteams = subteam_crud.get_by_team(db, team_id=team_id)
    return subteams

@router.put("/{subteam_id}", response_model=SubTeamResponse)
def update_subteam(
    subteam_id: int,
    subteam_update: SubTeamUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a subteam"""
    subteam = subteam_crud.update(db=db, subteam_id=subteam_id, subteam_update=subteam_update)
    if not subteam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subteam not found"
        )
    return subteam

@router.delete("/{subteam_id}")
def delete_subteam(
    subteam_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a subteam"""
    success = subteam_crud.delete(db=db, subteam_id=subteam_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subteam not found"
        )
    return {"message": "Subteam deleted successfully"} 