from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.tournament import Tournament
from app.schemas.tournament import TournamentCreate, TournamentUpdate
from app.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_get_namespace_version,
    cache_bump_namespace_version,
)


class TournamentCRUD:
    LIST_NAMESPACE = "tournaments:list"

    def create(self, db: Session, tournament: TournamentCreate) -> Tournament:
        db_tournament = Tournament(**tournament.model_dump())
        db.add(db_tournament)
        db.commit()
        db.refresh(db_tournament)
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return db_tournament

    def get(self, db: Session, tournament_id: int, use_cache: bool = True) -> Optional[Tournament]:
        cache_key = f"tournament:{tournament_id}"
        if use_cache:
            cached = cache_get(cache_key)
            if isinstance(cached, dict):
                return Tournament(**cached)

        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if tournament:
            cache_set(cache_key, tournament, 300)
        return tournament

    def get_by_name(self, db: Session, name: str) -> Optional[Tournament]:
        return db.query(Tournament).filter(Tournament.name == name).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Tournament]:
        version = cache_get_namespace_version(self.LIST_NAMESPACE)
        normalized_status = status or "all"
        normalized_search = (search or "").strip().lower()
        cache_key = (
            f"tournaments:list:v{version}:skip:{skip}:limit:{limit}:"
            f"status:{normalized_status}:search:{normalized_search}"
        )
        cached = cache_get(cache_key)
        if isinstance(cached, list):
            return [Tournament(**item) for item in cached if isinstance(item, dict)]

        query = db.query(Tournament)
        if status:
            query = query.filter(Tournament.status == status)
        if search:
            query = query.filter(Tournament.name.ilike(f"%{search}%"))

        tournaments = query.offset(skip).limit(limit).all()
        cache_set(cache_key, tournaments, 300)
        return tournaments

    def count_multi(self, db: Session, status: Optional[str] = None, search: Optional[str] = None) -> int:
        query = db.query(func.count(Tournament.id))
        if status:
            query = query.filter(Tournament.status == status)
        if search:
            query = query.filter(Tournament.name.ilike(f"%{search}%"))
        return query.scalar()

    def update(self, db: Session, tournament_id: int, tournament_update: TournamentUpdate) -> Optional[Tournament]:
        db_tournament = self.get(db, tournament_id, use_cache=False)
        if not db_tournament:
            return None

        update_data = tournament_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tournament, field, value)

        db.commit()
        db.refresh(db_tournament)

        cache_delete(f"tournament:{tournament_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return db_tournament

    def delete(self, db: Session, tournament_id: int) -> bool:
        db_tournament = self.get(db, tournament_id, use_cache=False)
        if not db_tournament:
            return False

        db.delete(db_tournament)
        db.commit()

        cache_delete(f"tournament:{tournament_id}")
        cache_bump_namespace_version(self.LIST_NAMESPACE)
        return True


tournament_crud = TournamentCRUD()
