from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
from pathlib import Path

from app.database import engine, Base
from app.routers import auth_router, teams_router, subteams_router, players_router, users_router
from app.utils.face_recognition import is_face_recognition_available
from app.cache import redis_client

# Keep schema ownership with Alembic by default.
if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)


def _parse_cors_origins() -> list[str]:
    """Parse comma-separated CORS origins from env."""
    raw = os.getenv("CORS_ORIGINS", "*").strip()
    if not raw:
        return ["*"]
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="Team Tournament API",
    description="A comprehensive API for managing teams, subteams, and players with face recognition capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
cors_origins = _parse_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if cors_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(subteams_router, prefix="/api/v1")
app.include_router(players_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

# Mount static files for uploads
uploads_dir = Path("uploads")
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Team Tournament API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    db_status = "healthy"
    redis_status = "healthy"

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except Exception:
        db_status = "unhealthy"

    try:
        redis_client.ping()
    except Exception:
        redis_status = "unavailable"

    overall_status = "healthy" if db_status == "healthy" else "degraded"
    return {
        "status": overall_status,
        "message": "API is running",
        "services": {
            "database": db_status,
            "redis": redis_status,
            "face_recognition": "available" if is_face_recognition_available() else "unavailable",
            "uploads_dir": str(uploads_dir.resolve()),
        },
    }

@app.get("/api-info")
def api_info():
    """API information endpoint"""
    return {
        "name": "Team Tournament API",
        "version": "1.0.0",
        "description": "A comprehensive API for managing teams, subteams, and players with face recognition capabilities",
        "features": [
            "Team and Subteam management",
            "Player management with face recognition",
            "JWT Authentication",
            "Redis caching",
            "File uploads",
            "Database migrations with Alembic"
        ],
        "mobile_readiness": {
            "auth": "JWT bearer token",
            "base_path": "/api/v1",
            "uploads_base_path": "/uploads",
            "face_recognition": "optional dependency",
        },
        "endpoints": {
            "auth": "/api/v1/auth",
            "teams": "/api/v1/teams",
            "subteams": "/api/v1/subteams",
            "players": "/api/v1/players",
            "users": "/api/v1/users"
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    detail = getattr(exc, "detail", None)
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": detail or "The requested resource was not found",
            "detail": detail or "The requested resource was not found",
        },
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "An unexpected error occurred"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
