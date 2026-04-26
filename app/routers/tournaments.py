from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.tournament import TournamentCreate, TournamentUpdate, TournamentResponse, TournamentStatus
from app.schemas.match import MatchResponse, TeamStanding
from app.schemas.pagination import Page, make_page
from app.schemas.player_match_stat import TopScorer
from app.crud.tournament import tournament_crud
from app.crud.match import match_crud
from app.crud.player_match_stat import player_match_stat_crud
from app.utils.auth import get_current_active_user, require_admin

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("/", response_model=TournamentResponse)
def create_tournament(
    tournament: TournamentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if tournament_crud.get_by_name(db, name=tournament.name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tournament name already exists")
    return tournament_crud.create(db=db, tournament=tournament)


@router.get("/", response_model=Page[TournamentResponse])
def get_tournaments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[TournamentStatus] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    status_val = status.value if status else None
    items = tournament_crud.get_multi(db=db, skip=skip, limit=limit, status=status_val, search=search)
    total = tournament_crud.count_multi(db=db, status=status_val, search=search)
    return make_page(items, total, skip, limit)


@router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    tournament = tournament_crud.get(db, tournament_id=tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    return tournament


@router.put("/{tournament_id}", response_model=TournamentResponse)
def update_tournament(
    tournament_id: int,
    tournament_update: TournamentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    tournament = tournament_crud.update(db=db, tournament_id=tournament_id, tournament_update=tournament_update)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    return tournament


@router.delete("/{tournament_id}")
def delete_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not tournament_crud.delete(db=db, tournament_id=tournament_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    return {"message": "Tournament deleted successfully"}


@router.get("/{tournament_id}/matches", response_model=Page[MatchResponse])
def get_tournament_matches(
    tournament_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not tournament_crud.get(db, tournament_id=tournament_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    items = match_crud.get_multi(db=db, skip=skip, limit=limit, tournament_id=tournament_id)
    total = match_crud.count_multi(db=db, tournament_id=tournament_id)
    return make_page(items, total, skip, limit)


@router.get("/{tournament_id}/standings", response_model=List[TeamStanding])
def get_tournament_standings(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not tournament_crud.get(db, tournament_id=tournament_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    return match_crud.get_standings(db=db, tournament_id=tournament_id)


@router.get("/{tournament_id}/top-scorers", response_model=List[TopScorer])
def get_top_scorers(
    tournament_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not tournament_crud.get(db, tournament_id=tournament_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    return player_match_stat_crud.get_top_scorers(db=db, tournament_id=tournament_id, limit=limit)
