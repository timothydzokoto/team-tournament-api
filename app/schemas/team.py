from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    coach_name: Optional[str] = None
    logo_url: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    coach_name: Optional[str] = None
    logo_url: Optional[str] = None

class TeamResponse(TeamBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime

class TeamList(BaseModel):
    teams: List[TeamResponse]
    total: int
    page: int
    size: int 