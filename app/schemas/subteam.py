from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class SubTeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    team_id: int

class SubTeamCreate(SubTeamBase):
    pass

class SubTeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[int] = None

class SubTeamResponse(SubTeamBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime

class SubTeamList(BaseModel):
    subteams: List[SubTeamResponse]
    total: int
    page: int
    size: int 