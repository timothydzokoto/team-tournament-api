#!/usr/bin/env python3
"""
Startup script for Team Tournament API
This script initializes the database and starts the server
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import sqlalchemy
        import redis
        import face_recognition
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "uploads",
        "uploads/images",
        "uploads/images/players",
        "uploads/images/teams"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def setup_database():
    """Setup database with Alembic"""
    print("🗄️ Setting up database...")
    
    try:
        # Initialize Alembic if not already done
        if not Path("alembic").exists():
            subprocess.run(["alembic", "init", "alembic"], check=True)
            print("✅ Alembic initialized")
        
        # Create initial migration
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial schema"], check=True)
        print("✅ Initial migration created")
        
        # Apply migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✅ Database migrations applied")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database setup failed: {e}")
        return False

def check_redis():
    """Check if Redis is running"""
    print("🔍 Checking Redis connection...")
    
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis is running")
        return True
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        print("Note: Redis is optional but recommended for caching")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Team Tournament API server...")
    print("=" * 50)
    
    try:
        subprocess.run([
            "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")

def main():
    """Main startup function"""
    print("🏆 Team Tournament API Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup database
    if not setup_database():
        print("⚠️ Database setup failed, but continuing...")
    
    # Check Redis
    check_redis()
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete! Starting server...")
    print("📚 API Documentation will be available at: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health")
    print("=" * 50)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main() 