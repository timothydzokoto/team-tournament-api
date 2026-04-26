from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerResponse, PlayerFaceMatch
from app.schemas.pagination import Page, make_page
from app.schemas.player_match_stat import (
    PlayerMatchStatResponse,
    PlayerStatSummary,
)
from app.crud.player import player_crud
from app.crud.subteam import subteam_crud
from app.crud.player_match_stat import player_match_stat_crud
from app.utils.auth import get_current_active_user, require_admin, require_coach_or_admin
from app.utils.face_recognition import (
    is_face_recognition_available,
    NoFaceDetectedError,
    MultipleFacesDetectedError,
    FaceImageDecodeError,
)
from app.utils.file_upload import save_image_file, get_file_url, validate_image_bytes

router = APIRouter(prefix="/players", tags=["players"])


def ensure_face_recognition_available() -> None:
    if not is_face_recognition_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Face recognition is unavailable. Install the optional dependency: pip install face-recognition",
        )


def raise_face_analysis_error(error: Exception) -> None:
    if isinstance(error, NoFaceDetectedError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No face detected in the image") from error
    if isinstance(error, MultipleFacesDetectedError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Multiple faces detected in the image") from error
    if isinstance(error, FaceImageDecodeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to decode image for face analysis") from error


# ── Player CRUD ──────────────────────────────────────────────────────────────

@router.post("/", response_model=PlayerResponse)
def create_player(
    player: PlayerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    if not subteam_crud.get(db, subteam_id=player.subteam_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subteam not found")
    if player.email and player_crud.get_by_email(db, email=player.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return player_crud.create(db=db, player=player)


@router.post("/face-match", response_model=PlayerFaceMatch)
def match_player_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    ensure_face_recognition_available()
    file_bytes = file.file.read()
    if not validate_image_bytes(file_bytes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")
    try:
        match_result = player_crud.find_player_by_face(db=db, face_image_bytes=file_bytes)
    except (NoFaceDetectedError, MultipleFacesDetectedError, FaceImageDecodeError) as error:
        raise_face_analysis_error(error)
    if not match_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching player found")
    return match_result


@router.get("/", response_model=Page[PlayerResponse])
def get_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    subteam_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    items = player_crud.get_multi(db=db, skip=skip, limit=limit, subteam_id=subteam_id, search=search)
    total = player_crud.count_multi(db=db, subteam_id=subteam_id, search=search)
    return make_page(items, total, skip, limit)


@router.get("/subteam/{subteam_id}", response_model=Page[PlayerResponse])
def get_players_by_subteam(
    subteam_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not subteam_crud.get(db, subteam_id=subteam_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subteam not found")
    items = player_crud.get_by_subteam(db, subteam_id=subteam_id, skip=skip, limit=limit)
    total = player_crud.count_multi(db=db, subteam_id=subteam_id)
    return make_page(items, total, skip, limit)


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    player = player_crud.get(db, player_id=player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player


@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(
    player_id: int,
    player_update: PlayerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    player = player_crud.update(db=db, player_id=player_id, player_update=player_update)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player


@router.delete("/{player_id}")
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not player_crud.delete(db=db, player_id=player_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return {"message": "Player deleted successfully"}


@router.post("/{player_id}/upload-face")
def upload_player_face(
    player_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    ensure_face_recognition_available()
    if not player_crud.get(db, player_id=player_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    try:
        file_bytes = file.file.read()
        if not validate_image_bytes(file_bytes):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")
        file_path = save_image_file(file, "players", content=file_bytes)
        file_url = get_file_url(file_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error saving image: {str(e)}")

    try:
        player_crud.update_face_encoding(db=db, player_id=player_id, face_image_bytes=file_bytes, face_image_url=file_url)
    except (NoFaceDetectedError, MultipleFacesDetectedError, FaceImageDecodeError) as error:
        raise_face_analysis_error(error)

    return {"message": "Face image uploaded successfully", "face_image_url": file_url}


# ── Player stats ─────────────────────────────────────────────────────────────

@router.get("/{player_id}/stats", response_model=List[PlayerMatchStatResponse])
def get_player_stats(
    player_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not player_crud.get(db, player_id=player_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player_match_stat_crud.get_by_player(db, player_id=player_id)


@router.get("/{player_id}/stats/summary", response_model=PlayerStatSummary)
def get_player_stats_summary(
    player_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    summary = player_match_stat_crud.get_player_summary(db, player_id=player_id)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return summary
