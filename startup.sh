#!/bin/bash

# Team Tournament API Startup Script
echo "🚀 Starting Team Tournament API Setup..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create uploads directory if it doesn't exist
echo "📁 Creating upload directories..."
mkdir -p uploads/images/players
mkdir -p uploads/images/teams

# Initialize Alembic if not already done
if [ ! -f "alembic/versions/001_initial_migration.py" ]; then
    echo "🗄️ Initializing database migrations..."
    alembic revision --autogenerate -m "Initial migration"
fi

# Apply database migrations
echo "🔄 Applying database migrations..."
alembic upgrade head

# Check if Redis is running (optional)
echo "🔍 Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️ Redis is not running (optional - caching will be disabled)"
    fi
else
    echo "⚠️ Redis CLI not found (optional - caching will be disabled)"
fi

# Start the server
echo "🌟 Starting the API server..."
echo "📚 API Documentation will be available at: http://localhost:8000/docs"
echo "📖 ReDoc Documentation will be available at: http://localhost:8000/redoc"
echo "🔗 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 