from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.match import Match
from app.models.team import Team
from app.schemas.match import MatchCreate, MatchUpdate, TeamStanding
from app.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_get_namespace_version,
    cache_bump_namespace_version,
)


class MatchCRUD:
    LIST_NAMESPACE = "matches:list"

    def create(self, db: Session, match: MatchCreate) -> Match:
        db_match = Match(**match.model_dump())
        db.add(db_match)
        db.commit()
        db.refresh(db_match)
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return db_match

    def get(self, db: Session, match_id: int, use_cache: bool = True) -> Optional[Match]:
        cache_key = f"match:{match_id}"
        if use_cache:
            cached = cache_get(cache_key)
            if isinstance(cached, dict):
                return Match(**cached)

        match = db.query(Match).filter(Match.id == match_id).first()
        if match:
            cache_set(cache_key, match, 300)
        return match

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        tournament_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Match]:
        version = cache_get_namespace_version(self.LIST_NAMESPACE)
        normalized_tournament = tournament_id if tournament_id is not None else "all"
        normalized_status = status or "all"
        cache_key = (
            f"matches:list:v{version}:skip:{skip}:limit:{limit}:"
            f"tournament:{normalized_tournament}:status:{normalized_status}"
        )
        cached = cache_get(cache_key)
        if isinstance(cached, list):
            return [Match(**item) for item in cached if isinstance(item, dict)]

        query = db.query(Match)
        if tournament_id:
            query = query.filter(Match.tournament_id == tournament_id)
        if status:
            query = query.filter(Match.status == status)

        matches = query.order_by(Match.scheduled_at).offset(skip).limit(limit).all()
        cache_set(cache_key, matches, 300)
        return matches

    def count_multi(self, db: Session, tournament_id: Optional[int] = None, status: Optional[str] = None) -> int:
        query = db.query(func.count(Match.id))
        if tournament_id:
            query = query.filter(Match.tournament_id == tournament_id)
        if status:
            query = query.filter(Match.status == status)
        return query.scalar()

    def update(self, db: Session, match_id: int, match_update: MatchUpdate) -> Optional[Match]:
        db_match = self.get(db, match_id, use_cache=False)
        if not db_match:
            return None

        update_data = match_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_match, field, value)

        db.commit()
        db.refresh(db_match)

        cache_delete(f"match:{match_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return db_match

    def delete(self, db: Session, match_id: int) -> bool:
        db_match = self.get(db, match_id, use_cache=False)
        if not db_match:
            return False

        db.delete(db_match)
        db.commit()

        cache_delete(f"match:{match_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return True

    def get_standings(self, db: Session, tournament_id: int) -> List[TeamStanding]:
        completed_matches = (
            db.query(Match)
            .filter(
                Match.tournament_id == tournament_id,
                Match.status == "completed",
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
            )
            .all()
        )

        stats: dict = defaultdict(lambda: {
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_for": 0, "goals_against": 0, "points": 0,
        })
        team_names: dict = {}

        def _team_name(team_id: int) -> str:
            if team_id not in team_names:
                team = db.query(Team).filter(Team.id == team_id).first()
                team_names[team_id] = team.name if team else f"Team {team_id}"
            return team_names[team_id]

        for match in completed_matches:
            h, a = match.home_team_id, match.away_team_id
            hs, as_ = match.home_score, match.away_score

            _team_name(h)
            _team_name(a)

            stats[h]["played"] += 1
            stats[a]["played"] += 1
            stats[h]["goals_for"] += hs
            stats[h]["goals_against"] += as_
            stats[a]["goals_for"] += as_
            stats[a]["goals_against"] += hs

            if hs > as_:
                stats[h]["wins"] += 1
                stats[h]["points"] += 3
                stats[a]["losses"] += 1
            elif hs == as_:
                stats[h]["draws"] += 1
                stats[h]["points"] += 1
                stats[a]["draws"] += 1
                stats[a]["points"] += 1
            else:
                stats[a]["wins"] += 1
                stats[a]["points"] += 3
                stats[h]["losses"] += 1

        standings = [
            TeamStanding(
                team_id=team_id,
                team_name=team_names[team_id],
                goal_difference=s["goals_for"] - s["goals_against"],
                **s,
            )
            for team_id, s in stats.items()
        ]
        standings.sort(key=lambda x: (-x.points, -x.goal_difference, -x.goals_for))
        return standings


match_crud = MatchCRUD()
