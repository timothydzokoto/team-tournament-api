from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.player_match_stat import (
    PlayerMatchStatCreate,
    PlayerMatchStatUpdate,
    PlayerMatchStatResponse,
)
from app.crud.player_match_stat import player_match_stat_crud
from app.crud.match import match_crud
from app.crud.player import player_crud
from app.utils.auth import get_current_active_user, require_admin, require_coach_or_admin

router = APIRouter(prefix="/matches", tags=["match stats"])


@router.post("/{match_id}/stats", response_model=PlayerMatchStatResponse)
def record_player_stat(
    match_id: int,
    stat: PlayerMatchStatCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    if not match_crud.get(db, match_id=match_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if not player_crud.get(db, player_id=stat.player_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    if player_match_stat_crud.get(db, match_id=match_id, player_id=stat.player_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stats already recorded for this player in this match. Use PUT to update.",
        )
    return player_match_stat_crud.create(db=db, match_id=match_id, stat=stat)


@router.get("/{match_id}/stats", response_model=List[PlayerMatchStatResponse])
def get_match_stats(
    match_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not match_crud.get(db, match_id=match_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return player_match_stat_crud.get_by_match(db, match_id=match_id)


@router.put("/{match_id}/stats/{player_id}", response_model=PlayerMatchStatResponse)
def update_player_stat(
    match_id: int,
    player_id: int,
    stat_update: PlayerMatchStatUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    stat = player_match_stat_crud.update(db=db, match_id=match_id, player_id=player_id, stat_update=stat_update)
    if not stat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stat record not found")
    return stat


@router.delete("/{match_id}/stats/{player_id}")
def delete_player_stat(
    match_id: int,
    player_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not player_match_stat_crud.delete(db=db, match_id=match_id, player_id=player_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stat record not found")
    return {"message": "Stat record deleted successfully"}
