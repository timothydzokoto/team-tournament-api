from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.schemas.pagination import Page, make_page
from app.crud.team import team_crud
from app.utils.auth import get_current_active_user, require_admin, require_coach_or_admin
from app.utils.file_upload import save_image_file, get_file_url, validate_image_bytes, delete_file

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("/", response_model=TeamResponse)
def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    if team_crud.get_by_name(db, name=team.name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team name already exists")
    return team_crud.create(db=db, team=team)


@router.get("/", response_model=Page[TeamResponse])
def get_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    items = team_crud.get_multi(db=db, skip=skip, limit=limit, search=search)
    total = team_crud.count_multi(db=db, search=search)
    return make_page(items, total, skip, limit)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    team = team_crud.get(db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_update: TeamUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    team = team_crud.update(db=db, team_id=team_id, team_update=team_update)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.post("/{team_id}/upload-logo")
def upload_team_logo(
    team_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """Upload or replace a team's logo image"""
    team = team_crud.get(db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    try:
        file_bytes = file.file.read()
        if not validate_image_bytes(file_bytes):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")
        file_path = save_image_file(file, "teams", content=file_bytes)
        file_url = get_file_url(file_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error saving image: {str(e)}")

    if team.logo_url:
        delete_file(team.logo_url.lstrip("/"))

    team_crud.update(db=db, team_id=team_id, team_update=TeamUpdate(logo_url=file_url))
    return {"message": "Logo uploaded successfully", "logo_url": file_url}


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not team_crud.delete(db=db, team_id=team_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return {"message": "Team deleted successfully"}
