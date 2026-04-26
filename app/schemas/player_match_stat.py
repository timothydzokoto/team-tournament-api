from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class PlayerMatchStatCreate(BaseModel):
    player_id: int
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    minutes_played: int = 0


class PlayerMatchStatUpdate(BaseModel):
    goals: Optional[int] = None
    assists: Optional[int] = None
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    minutes_played: Optional[int] = None


class PlayerMatchStatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    player_id: int
    goals: int
    assists: int
    yellow_cards: int
    red_cards: int
    minutes_played: int
    created_at: datetime
    updated_at: datetime


class PlayerStatSummary(BaseModel):
    player_id: int
    player_name: str
    matches_played: int
    total_goals: int
    total_assists: int
    total_yellow_cards: int
    total_red_cards: int
    total_minutes_played: int


class TopScorer(BaseModel):
    player_id: int
    player_name: str
    goals: int
    assists: int
    matches_played: int
