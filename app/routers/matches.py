from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.match import MatchCreate, MatchUpdate, MatchResponse, MatchStatus
from app.schemas.pagination import Page, make_page
from app.crud.match import match_crud
from app.crud.tournament import tournament_crud
from app.crud.team import team_crud
from app.utils.auth import get_current_active_user, require_admin, require_coach_or_admin

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/", response_model=MatchResponse)
def create_match(
    match: MatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not tournament_crud.get(db, tournament_id=match.tournament_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if not team_crud.get(db, team_id=match.home_team_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Home team not found")
    if not team_crud.get(db, team_id=match.away_team_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Away team not found")
    return match_crud.create(db=db, match=match)


@router.get("/", response_model=Page[MatchResponse])
def get_matches(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tournament_id: Optional[int] = Query(None),
    status: Optional[MatchStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    status_val = status.value if status else None
    items = match_crud.get_multi(db=db, skip=skip, limit=limit, tournament_id=tournament_id, status=status_val)
    total = match_crud.count_multi(db=db, tournament_id=tournament_id, status=status_val)
    return make_page(items, total, skip, limit)


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    match = match_crud.get(db, match_id=match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


@router.put("/{match_id}", response_model=MatchResponse)
def update_match(
    match_id: int,
    match_update: MatchUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    match = match_crud.update(db=db, match_id=match_id, match_update=match_update)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


@router.delete("/{match_id}")
def delete_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not match_crud.delete(db=db, match_id=match_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return {"message": "Match deleted successfully"}
