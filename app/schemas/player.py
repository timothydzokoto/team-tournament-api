from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PlayerBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    is_active: bool = True
    subteam_id: int

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    is_active: Optional[bool] = None
    subteam_id: Optional[int] = None

class PlayerResponse(PlayerBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    face_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class PlayerList(BaseModel):
    players: List[PlayerResponse]
    total: int
    page: int
    size: int

class PlayerFaceMatch(BaseModel):
    player_id: int
    player_name: str
    confidence: float
    face_image_url: Optional[str] = None 