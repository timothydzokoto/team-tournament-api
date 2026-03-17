from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.cache
from app.database import Base, get_db
from app.main import app as fastapi_app
import app.models  # noqa: F401


SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class FakeRedisClient:
    def setex(self, *args, **kwargs):
        return None

    def get(self, *args, **kwargs):
        return None

    def delete(self, *args, **kwargs):
        return None

    def scan_iter(self, *args, **kwargs):
        return []

    def incr(self, *args, **kwargs):
        return 1

    def ping(self):
        return True


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.cache.redis_client = FakeRedisClient()
    fastapi_app.dependency_overrides[get_db] = override_get_db
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    yield
    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(fastapi_app) as test_client:
        yield test_client
