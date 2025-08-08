from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerResponse, PlayerFaceMatch
from app.crud.player import player_crud
from app.crud.subteam import subteam_crud
from app.utils.auth import get_current_active_user
from app.utils.file_upload import save_image_file, get_file_url

router = APIRouter(prefix="/players", tags=["players"])

@router.post("/", response_model=PlayerResponse)
def create_player(
    player: PlayerCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new player"""
    # Check if subteam exists
    subteam = subteam_crud.get(db, subteam_id=player.subteam_id)
    if not subteam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subteam not found"
        )
    
    # Check if email is unique (if provided)
    if player.email:
        existing_player = player_crud.get_by_email(db, email=player.email)
        if existing_player:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    return player_crud.create(db=db, player=player)

@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a player by ID"""
    player = player_crud.get(db, player_id=player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return player

@router.get("/", response_model=List[PlayerResponse])
def get_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    subteam_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all players with optional filtering"""
    players = player_crud.get_multi(
        db=db, 
        skip=skip, 
        limit=limit, 
        subteam_id=subteam_id,
        search=search
    )
    return players

@router.get("/subteam/{subteam_id}", response_model=List[PlayerResponse])
def get_players_by_subteam(
    subteam_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all players for a specific subteam"""
    # Check if subteam exists
    subteam = subteam_crud.get(db, subteam_id=subteam_id)
    if not subteam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subteam not found"
        )
    
    players = player_crud.get_by_subteam(db, subteam_id=subteam_id)
    return players

@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(
    player_id: int,
    player_update: PlayerUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a player"""
    player = player_crud.update(db=db, player_id=player_id, player_update=player_update)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return player

@router.delete("/{player_id}")
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a player"""
    success = player_crud.delete(db=db, player_id=player_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return {"message": "Player deleted successfully"}

@router.post("/{player_id}/upload-face")
def upload_player_face(
    player_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Upload a face image for a player"""
    # Check if player exists
    player = player_crud.get(db, player_id=player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Save the image file
    try:
        file_path = save_image_file(file, "players")
        file_url = get_file_url(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error saving image: {str(e)}"
        )
    
    # Read file bytes for face encoding
    file.file.seek(0)
    file_bytes = file.file.read()
    
    # Update player with face encoding
    updated_player = player_crud.update_face_encoding(
        db=db, 
        player_id=player_id, 
        face_image_bytes=file_bytes,
        face_image_url=file_url
    )
    
    if not updated_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected in the image"
        )
    
    return {"message": "Face image uploaded successfully", "face_image_url": file_url}

@router.post("/face-match", response_model=PlayerFaceMatch)
def match_player_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Match a face image against stored player faces"""
    # Read file bytes
    file_bytes = file.file.read()
    
    # Find matching player
    match_result = player_crud.find_player_by_face(db=db, face_image_bytes=file_bytes)
    
    if not match_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching player found"
        )
    
    return match_result 