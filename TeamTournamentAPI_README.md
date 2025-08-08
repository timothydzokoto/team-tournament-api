# 🏆 Team Tournament Management API – FastAPI Backend

This guide outlines how to build a **FastAPI** backend for managing teams, sub-teams, and players in a tournament. It includes real-time **face verification**, **Redis caching**, and **Alembic** for database migrations.

---

## 📦 Tech Stack

| Component     | Tech                  |
|---------------|------------------------|
| API Framework | FastAPI                |
| ORM           | SQLAlchemy             |
| DB Migrations | Alembic                |
| Database      | PostgreSQL (or SQLite) |
| Caching       | Redis                  |
| Media Uploads | Multipart              |
| Face Match    | `face_recognition`     |

---

## 📁 Project Structure

```plaintext
app/
├── main.py
├── database.py
├── cache.py
├── models/
├── schemas/
├── crud/
├── routers/
├── utils/
alembic/
.env
```

---

## ✅ Step-by-Step Setup

### 1. Create Project and Virtual Environment

```bash
mkdir team-tournament-api && cd team-tournament-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install fastapi[all] sqlalchemy alembic psycopg2-binary redis python-multipart face_recognition uvicorn python-dotenv
```

### 3. Configure Database Connection

In `.env`:

```env
DATABASE_URL=postgresql://postgres:password@localhost/tournament
```

In `app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
```

---

### 4. Define Models

- `Team` → has many `SubTeams`
- `SubTeam` → belongs to `Team`, has many `Players`
- `Player` → belongs to a `SubTeam`, stores face image

Example: `app/models/team.py`

```python
from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    coach_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    subteams = relationship("SubTeam", back_populates="parent_team")
```

---

### 5. Set Up Alembic

```bash
alembic init alembic
```

In `alembic/env.py`:

```python
from app.models import team, subteam, player
from app.database import Base
target_metadata = Base.metadata
```

Then:

```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

### 6. Redis Caching

`app/cache.py`

```python
import redis, json

redis_client = redis.Redis(host="localhost", port=6379)

def cache_set(key, value, expiry=300):
    redis_client.setex(key, expiry, json.dumps(value))

def cache_get(key):
    data = redis_client.get(key)
    return json.loads(data) if data else None
```

Use this in your player/team GET endpoints to cache responses.

---

### 7. Add Face Recognition

`app/utils/face.py`:

```python
import face_recognition

def encode_face(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None

def match_faces(known_encoding, unknown_encoding):
    return face_recognition.compare_faces([known_encoding], unknown_encoding)[0]
```

---

### 8. API Routers and Endpoints

Example for Team (`app/routers/team.py`):

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamOut
from app.cache import cache_get, cache_set

router = APIRouter()

@router.post("/", response_model=TeamOut)
def create_team(team: TeamCreate, db: Session = Depends(SessionLocal)):
    db_team = Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(SessionLocal)):
    key = f"team:{team_id}"
    cached = cache_get(key)
    if cached:
        return cached
    team = db.query(Team).get(team_id)
    if team:
        cache_set(key, team.__dict__)
        return team
```

---

### 9. Run the App

```bash
uvicorn app.main:app --reload
```

---

## 🚀 Optional Improvements

| Feature              | Tech/Suggestion                 |
|----------------------|----------------------------------|
| Auth & Roles         | OAuth2 / JWT                    |
| File Storage         | Amazon S3 or local mount        |
| Testing              | Pytest + TestClient             |
| Admin Dashboard      | FastAPI Admin / React Frontend  |
| Deployment           | Docker + Gunicorn + Nginx       |
| Real-time Updates    | WebSockets or Pusher            |

---

## 📌 Next Steps

- [ ] Define all schemas using `pydantic`
- [ ] Build full CRUD in `crud/`
- [ ] Add upload endpoints for face image
- [ ] Integrate Redis in player face search
- [ ] Add search and leaderboard endpoints