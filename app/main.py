from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

from app.database import engine, Base
from app.routers import auth_router, teams_router, subteams_router, players_router, users_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team Tournament API",
    description="A comprehensive API for managing teams, subteams, and players with face recognition capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
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
    return {"status": "healthy", "message": "API is running"}

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
    return {"error": "Not found", "message": "The requested resource was not found"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "message": "An unexpected error occurred"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 