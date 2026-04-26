from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MatchStatus(str, Enum):
    scheduled = "scheduled"
    ongoing = "ongoing"
    completed = "completed"
    cancelled = "cancelled"


class MatchBase(BaseModel):
    tournament_id: int
    home_team_id: int
    away_team_id: int
    scheduled_at: datetime
    venue: Optional[str] = None
    status: MatchStatus = MatchStatus.scheduled


class MatchCreate(MatchBase):
    @model_validator(mode="after")
    def teams_must_differ(self):
        if self.home_team_id == self.away_team_id:
            raise ValueError("home_team_id and away_team_id must be different")
        return self


class MatchUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    venue: Optional[str] = None
    status: Optional[MatchStatus] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None


class MatchResponse(MatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class TeamStanding(BaseModel):
    team_id: int
    team_name: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
