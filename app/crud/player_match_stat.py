from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.player_match_stat import PlayerMatchStat
from app.models.match import Match
from app.models.player import Player
from app.schemas.player_match_stat import (
    PlayerMatchStatCreate,
    PlayerMatchStatUpdate,
    PlayerStatSummary,
    TopScorer,
)


class PlayerMatchStatCRUD:

    def create(self, db: Session, match_id: int, stat: PlayerMatchStatCreate) -> PlayerMatchStat:
        db_stat = PlayerMatchStat(match_id=match_id, **stat.model_dump())
        db.add(db_stat)
        db.commit()
        db.refresh(db_stat)
        return db_stat

    def get(self, db: Session, match_id: int, player_id: int) -> Optional[PlayerMatchStat]:
        return (
            db.query(PlayerMatchStat)
            .filter(PlayerMatchStat.match_id == match_id, PlayerMatchStat.player_id == player_id)
            .first()
        )

    def get_by_match(self, db: Session, match_id: int) -> List[PlayerMatchStat]:
        return db.query(PlayerMatchStat).filter(PlayerMatchStat.match_id == match_id).all()

    def get_by_player(self, db: Session, player_id: int) -> List[PlayerMatchStat]:
        return db.query(PlayerMatchStat).filter(PlayerMatchStat.player_id == player_id).all()

    def update(
        self, db: Session, match_id: int, player_id: int, stat_update: PlayerMatchStatUpdate
    ) -> Optional[PlayerMatchStat]:
        db_stat = self.get(db, match_id=match_id, player_id=player_id)
        if not db_stat:
            return None
        for field, value in stat_update.model_dump(exclude_unset=True).items():
            setattr(db_stat, field, value)
        db.commit()
        db.refresh(db_stat)
        return db_stat

    def delete(self, db: Session, match_id: int, player_id: int) -> bool:
        db_stat = self.get(db, match_id=match_id, player_id=player_id)
        if not db_stat:
            return False
        db.delete(db_stat)
        db.commit()
        return True

    def get_player_summary(self, db: Session, player_id: int) -> Optional[PlayerStatSummary]:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return None

        row = (
            db.query(
                func.count(PlayerMatchStat.id).label("matches_played"),
                func.coalesce(func.sum(PlayerMatchStat.goals), 0).label("total_goals"),
                func.coalesce(func.sum(PlayerMatchStat.assists), 0).label("total_assists"),
                func.coalesce(func.sum(PlayerMatchStat.yellow_cards), 0).label("total_yellow_cards"),
                func.coalesce(func.sum(PlayerMatchStat.red_cards), 0).label("total_red_cards"),
                func.coalesce(func.sum(PlayerMatchStat.minutes_played), 0).label("total_minutes_played"),
            )
            .filter(PlayerMatchStat.player_id == player_id)
            .one()
        )

        return PlayerStatSummary(
            player_id=player_id,
            player_name=player.full_name,
            matches_played=row.matches_played,
            total_goals=row.total_goals,
            total_assists=row.total_assists,
            total_yellow_cards=row.total_yellow_cards,
            total_red_cards=row.total_red_cards,
            total_minutes_played=row.total_minutes_played,
        )

    def get_top_scorers(self, db: Session, tournament_id: int, limit: int = 10) -> List[TopScorer]:
        match_ids = [
            row[0]
            for row in db.query(Match.id).filter(Match.tournament_id == tournament_id).all()
        ]
        if not match_ids:
            return []

        rows = (
            db.query(
                PlayerMatchStat.player_id,
                func.coalesce(func.sum(PlayerMatchStat.goals), 0).label("goals"),
                func.coalesce(func.sum(PlayerMatchStat.assists), 0).label("assists"),
                func.count(PlayerMatchStat.id).label("matches_played"),
            )
            .filter(PlayerMatchStat.match_id.in_(match_ids))
            .group_by(PlayerMatchStat.player_id)
            .order_by(func.sum(PlayerMatchStat.goals).desc())
            .limit(limit)
            .all()
        )

        scorers = []
        for row in rows:
            player = db.query(Player).filter(Player.id == row.player_id).first()
            if player:
                scorers.append(
                    TopScorer(
                        player_id=row.player_id,
                        player_name=player.full_name,
                        goals=row.goals,
                        assists=row.assists,
                        matches_played=row.matches_played,
                    )
                )
        return scorers


player_match_stat_crud = PlayerMatchStatCRUD()
