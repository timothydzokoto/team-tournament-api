# Team Tournament API Testing Guide

This document explains how to test the application locally in a repeatable way.

## 1. Prerequisites

- Python `3.8+`
- `pip`
- Optional: Redis (`localhost:6379`) for cache checks
- Optional: `face-recognition` package for face endpoints

## 2. Environment Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy/update environment variables (if needed) in `.env`:

```env
DATABASE_URL=sqlite:///./tournament.db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=uploads
MAX_FILE_SIZE=5242880
```

Apply DB migrations:

```powershell
alembic upgrade head
```

## 3. Start the API

Run the server:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected:

- API root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`

## 4. Quick Smoke Test (Script)

In a second terminal (with venv active), run:

```powershell
python test_api.py
```

What this validates:

- Health endpoint
- Register/login flow
- Create + read/list for teams
- Create + read for subteams
- Create + read/list for players

Expected final output includes:

- `All tests completed successfully!`

## 5. Automated API Test Suite

Run the repeatable backend test suite:

```powershell
pytest tests/test_api_endpoints.py
```

This validates:

- health response shape
- auth register/login/me
- protected route behavior
- team/subteam/player core CRUD flow
- invalid subteam rejection
- invalid image rejection for face routes

## 6. Manual API Test (PowerShell)

Use this when you want to test endpoint behavior directly.

### 5.1 Register

```powershell
$base = "http://localhost:8000/api/v1"
$regBody = @{
  username = "manualuser"
  email = "manualuser@example.com"
  password = "StrongPass123!"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "$base/auth/register" -ContentType "application/json" -Body $regBody
```

### 5.2 Login and store token

```powershell
$loginBody = @{
  username = "manualuser"
  password = "StrongPass123!"
} | ConvertTo-Json

$login = Invoke-RestMethod -Method Post -Uri "$base/auth/login" -ContentType "application/json" -Body $loginBody
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
```

### 5.3 Create team

```powershell
$teamBody = @{
  name = "Manual Team"
  description = "Created from TESTME flow"
  coach_name = "Coach Manual"
} | ConvertTo-Json

$team = Invoke-RestMethod -Method Post -Uri "$base/teams" -Headers $headers -ContentType "application/json" -Body $teamBody
$teamId = $team.id
```

### 5.4 Create subteam

```powershell
$subBody = @{
  name = "Manual Subteam"
  description = "Subteam for manual test"
  team_id = $teamId
} | ConvertTo-Json

$sub = Invoke-RestMethod -Method Post -Uri "$base/subteams" -Headers $headers -ContentType "application/json" -Body $subBody
$subId = $sub.id
```

### 5.5 Create player

```powershell
$playerBody = @{
  first_name = "Jane"
  last_name = "Doe"
  email = "jane.doe@example.com"
  phone = "+15550001111"
  position = "Forward"
  jersey_number = 9
  height = 172
  weight = 64
  is_active = $true
  subteam_id = $subId
} | ConvertTo-Json

$player = Invoke-RestMethod -Method Post -Uri "$base/players" -Headers $headers -ContentType "application/json" -Body $playerBody
$playerId = $player.id
```

### 5.6 Verify protected reads

```powershell
Invoke-RestMethod -Method Get -Uri "$base/auth/me" -Headers $headers
Invoke-RestMethod -Method Get -Uri "$base/teams" -Headers $headers
Invoke-RestMethod -Method Get -Uri "$base/subteams" -Headers $headers
Invoke-RestMethod -Method Get -Uri "$base/players" -Headers $headers
```

## 7. Face Endpoint Testing (Optional)

Face routes require the optional dependency.

Install:

```powershell
pip install face-recognition
```

If missing, face routes should return `503` with a clear message.

### 6.1 Upload face

```powershell
$imgPath = "C:\path\to\face.jpg"
$form = @{ file = Get-Item $imgPath }
Invoke-RestMethod -Method Post -Uri "$base/players/$playerId/upload-face" -Headers $headers -Form $form
```

Expected:

- `message: Face image uploaded successfully`
- `face_image_url` returned

### 6.2 Match face

```powershell
$form = @{ file = Get-Item "C:\path\to\probe.jpg" }
Invoke-RestMethod -Method Post -Uri "$base/players/face-match" -Headers $headers -Form $form
```

Expected:

- On match: `player_id`, `player_name`, `confidence`
- On no match: HTTP `404` with `No matching player found`

## 8. Basic Negative Tests

- Call protected route without token -> expect `401`
- Register existing username/email -> expect `400`
- Create player with invalid `subteam_id` -> expect `404`
- Upload non-image file to face route -> expect `400`/validation failure

## 9. Troubleshooting

- `Connection refused`:
  - Ensure server is running on `http://localhost:8000`
- `401 Unauthorized`:
  - Token missing/expired; login again
- `503 face recognition unavailable`:
  - Install optional package: `pip install face-recognition`
- DB errors:
  - Re-run migrations: `alembic upgrade head`
- CORS errors from frontend:
  - Set `CORS_ORIGINS` in `.env` and restart server

## 10. Pass Criteria

The application passes this test guide when:

- Health endpoint returns `200`
- `pytest tests/test_api_endpoints.py` passes
- Auth register/login/me flows work
- Team/subteam/player CRUD create+read/list work
- Face upload/match behaves correctly (or returns controlled `503` when dependency is absent)
- Error paths return expected HTTP status codes and readable messages
