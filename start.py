#!/usr/bin/env python3
"""
Startup script for Team Tournament API.
This script initializes the database and starts the server.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    print("Checking dependencies...")

    required_modules = ["fastapi", "sqlalchemy", "redis"]
    missing_modules = [name for name in required_modules if importlib.util.find_spec(name) is None]
    if missing_modules:
        print(f"Missing dependency: {', '.join(missing_modules)}")
        print("Please run: pip install -r requirements.txt")
        return False

    if importlib.util.find_spec("face_recognition") is None:
        print("Optional dependency missing: face_recognition")
        print("Face endpoints will return 503 until it is installed.")

    print("Required dependencies are installed")
    return True


def create_directories() -> None:
    """Create necessary directories."""
    print("Creating directories...")

    directories = [
        "uploads",
        "uploads/images",
        "uploads/images/players",
        "uploads/images/teams",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    print("Directories created")


def setup_database() -> bool:
    """Setup database with Alembic."""
    print("Setting up database...")

    try:
        # Initialize Alembic if not already done.
        if not Path("alembic").exists():
            subprocess.run(["alembic", "init", "alembic"], check=True)
            print("Alembic initialized")

        # Create initial migration.
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial schema"], check=True)
        print("Initial migration created")

        # Apply migrations.
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Database migrations applied")

        return True
    except subprocess.CalledProcessError as exc:
        print(f"Database setup failed: {exc}")
        return False


def check_redis() -> bool:
    """Check if Redis is running."""
    print("Checking Redis connection...")

    try:
        import redis

        client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        client.ping()
        print("Redis is running")
        return True
    except Exception as exc:
        print(f"Redis connection failed: {exc}")
        print("Redis is optional but recommended for caching")
        return False


def start_server() -> None:
    """Start the FastAPI server."""
    print("Starting Team Tournament API server...")
    print("=" * 50)

    try:
        subprocess.run(
            [
                "uvicorn",
                "app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ]
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as exc:
        print(f"Server failed to start: {exc}")


def main() -> None:
    """Main startup function."""
    print("Team Tournament API Startup")
    print("=" * 40)

    if not check_dependencies():
        sys.exit(1)

    create_directories()

    if not setup_database():
        print("Database setup failed, but continuing...")

    check_redis()

    print("\n" + "=" * 50)
    print("Setup complete. Starting server...")
    print("API documentation: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    print("=" * 50)

    start_server()


if __name__ == "__main__":
    main()
