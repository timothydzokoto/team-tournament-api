# Team Tournament API

FastAPI REST API for managing teams, subteams, players, and users, with JWT authentication, Redis-backed caching utilities, and face recognition for player matching.

## Features

- Team, subteam, player, and user CRUD APIs
- JWT auth (`register`, `login`, `me`)
- Face upload and face-match endpoints for players
- SQLAlchemy models with Alembic migrations
- Redis cache helpers with graceful fallback when Redis is unavailable
- Swagger and ReDoc documentation

## Tech Stack

- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL (recommended) or SQLite (default)
- Redis (optional)
- `python-jose` + `passlib` for JWT auth
- `face_recognition` for facial encoding and matching

## Project Structure

```text
team-tournament-api/
|-- app/
|   |-- main.py
|   |-- database.py
|   |-- cache.py
|   |-- models/
|   |-- schemas/
|   |-- crud/
|   |-- routers/
|   `-- utils/
|-- alembic/
|-- requirements.txt
|-- alembic.ini
|-- Dockerfile
|-- start.py
|-- startup.sh
`-- README.md
```

## Prerequisites

- Python 3.8+
- Redis (optional)
- PostgreSQL (optional, recommended for production)

## Local Setup

1. Create and activate a virtual environment.

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows PowerShell
venv\Scripts\Activate.ps1
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Configure environment variables.

A local `.env` is already present in this repo. Review and adjust it for your environment.

Example values:

```env
# Database
DATABASE_URL=sqlite:///./tournament.db
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tournament

# Redis (optional)
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Uploads
UPLOAD_DIR=uploads
MAX_FILE_SIZE=5242880

# CORS (comma-separated; use * for open dev mode)
CORS_ORIGINS=http://localhost:8081,http://localhost:19006,http://192.168.1.20:8081
```

4. Apply database migrations.

```bash
alembic upgrade head
```

5. Start the API.

```bash
uvicorn app.main:app --reload
```

API base URL: `http://localhost:8000`

## React Native Integration

Use a reachable API host, not `localhost`, when testing on devices/emulators.

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://127.0.0.1:8000`
- Physical phone on same Wi-Fi: `http://<YOUR_PC_LAN_IP>:8000` (for example `http://192.168.1.20:8000`)

If you use Expo web or a web frontend, set `CORS_ORIGINS` in `.env` to your app origin(s), then restart the API server.

Example React Native API client:

```ts
// api/client.ts
const API_BASE_URL = "http://10.0.2.2:8000/api/v1"; // change per platform/device

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(`HTTP ${res.status}: ${message}`);
  }
  return res.json() as Promise<T>;
}
```

Login flow example:

```ts
type LoginResponse = { access_token: string; token_type: string };

const login = await apiFetch<LoginResponse>("/auth/login", {
  method: "POST",
  body: JSON.stringify({ username: "admin", password: "securepassword" }),
});

setAccessToken(login.access_token);
const teams = await apiFetch("/teams");
```

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- API info: `http://localhost:8000/api-info`
- Health check: `http://localhost:8000/health`

## Authentication Flow

1. Register

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepassword"
  }'
```

2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "securepassword"
  }'
```

3. Use token

```bash
curl -X GET "http://localhost:8000/api/v1/teams" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Endpoints

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Teams

- `GET /api/v1/teams`
- `POST /api/v1/teams`
- `GET /api/v1/teams/{team_id}`
- `PUT /api/v1/teams/{team_id}`
- `DELETE /api/v1/teams/{team_id}`

### Subteams

- `GET /api/v1/subteams`
- `POST /api/v1/subteams`
- `GET /api/v1/subteams/{subteam_id}`
- `PUT /api/v1/subteams/{subteam_id}`
- `DELETE /api/v1/subteams/{subteam_id}`
- `GET /api/v1/subteams/team/{team_id}`

### Players

- `GET /api/v1/players`
- `POST /api/v1/players`
- `GET /api/v1/players/{player_id}`
- `PUT /api/v1/players/{player_id}`
- `DELETE /api/v1/players/{player_id}`
- `GET /api/v1/players/subteam/{subteam_id}`
- `POST /api/v1/players/{player_id}/upload-face`
- `POST /api/v1/players/face-match`

### Users (superuser only)

- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PUT /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`

## Face Recognition Notes

This project imports `face_recognition` in runtime code. The package is currently commented out in `requirements.txt`, so you need to install it explicitly if face endpoints are used.

Example:

```bash
pip install face-recognition
```

Depending on OS, you may also need system-level dependencies (for example `cmake`, `dlib` build tooling).

## Docker

Build and run:

```bash
docker build -t team-tournament-api .
docker run -p 8000:8000 team-tournament-api
```

## Testing

- Run tests:

```bash
pytest tests/test_api_endpoints.py
```

- Optional manual smoke test script:

```bash
python test_api.py
```

## Backend Readiness For Mobile

Before connecting an Expo app to this API, verify these backend conditions:

- `SECRET_KEY` is set to a strong non-default value.
- `CORS_ORIGINS` includes your Expo web origin when testing on web.
- The API is reachable from emulator, simulator, and physical devices using the correct host.
- `/health` reports database status correctly and exposes service capability info.
- Image uploads respect `MAX_FILE_SIZE` and reject invalid images with `400`.
- Face endpoints are treated as optional and return `503` when `face-recognition` is not installed.
- The automated API test suite passes before frontend integration starts.

## Production Notes

- Replace `SECRET_KEY` with a strong secret
- Restrict CORS in `app/main.py`
- Use PostgreSQL instead of SQLite
- Run with a production server/process model (for example Gunicorn + Uvicorn workers)
- Ensure Redis and DB observability/monitoring are configured
