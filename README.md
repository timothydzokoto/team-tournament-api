# 🏆 Team Tournament API

A comprehensive FastAPI-based REST API for managing teams, subteams, and players with advanced features including face recognition, Redis caching, and JWT authentication.

## ✨ Features

- **Team & Subteam Management**: Complete CRUD operations for teams and subteams
- **Player Management**: Comprehensive player profiles with face recognition
- **Face Recognition**: Upload and match player faces using AI
- **JWT Authentication**: Secure user authentication and authorization
- **Redis Caching**: High-performance caching for improved response times
- **File Uploads**: Image upload support for player faces and team logos
- **Database Migrations**: Alembic-based schema management
- **RESTful API**: Well-structured REST endpoints with proper HTTP status codes
- **Comprehensive Documentation**: Auto-generated API docs with Swagger/ReDoc

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **API Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | PostgreSQL (production) / SQLite (development) |
| **Caching** | Redis |
| **Authentication** | JWT (python-jose + passlib) |
| **Face Recognition** | face_recognition library |
| **Migrations** | Alembic |
| **File Storage** | Local filesystem |
| **Documentation** | Swagger/ReDoc |

## 📁 Project Structure

```
team-tournament-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── cache.py             # Redis caching utilities
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── team.py
│   │   ├── subteam.py
│   │   ├── player.py
│   │   └── user.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── team.py
│   │   ├── subteam.py
│   │   ├── player.py
│   │   └── user.py
│   ├── crud/               # CRUD operations
│   │   ├── __init__.py
│   │   ├── team.py
│   │   ├── subteam.py
│   │   ├── player.py
│   │   └── user.py
│   ├── routers/            # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── teams.py
│   │   ├── subteams.py
│   │   ├── players.py
│   │   └── users.py
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── auth.py
│       ├── face_recognition.py
│       └── file_upload.py
├── alembic/                # Database migrations
├── uploads/                # File uploads
├── requirements.txt
├── alembic.ini
├── Dockerfile
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Redis (optional, for caching)
- PostgreSQL (optional, for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd team-tournament-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # Create initial migration
   alembic revision --autogenerate -m "Initial migration"
   
   # Apply migrations
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Info**: http://localhost:8000/api-info

## 🔐 Authentication

The API uses JWT-based authentication. Here's how to use it:

### 1. Register a user
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepassword"
  }'
```

### 2. Login to get access token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "securepassword"
  }'
```

### 3. Use the token in subsequent requests
```bash
curl -X GET "http://localhost:8000/api/v1/teams" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🏗 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get access token
- `GET /api/v1/auth/me` - Get current user info

### Teams
- `GET /api/v1/teams` - List all teams
- `POST /api/v1/teams` - Create new team
- `GET /api/v1/teams/{team_id}` - Get team by ID
- `PUT /api/v1/teams/{team_id}` - Update team
- `DELETE /api/v1/teams/{team_id}` - Delete team

### Subteams
- `GET /api/v1/subteams` - List all subteams
- `POST /api/v1/subteams` - Create new subteam
- `GET /api/v1/subteams/{subteam_id}` - Get subteam by ID
- `PUT /api/v1/subteams/{subteam_id}` - Update subteam
- `DELETE /api/v1/subteams/{subteam_id}` - Delete subteam
- `GET /api/v1/subteams/team/{team_id}` - Get subteams by team

### Players
- `GET /api/v1/players` - List all players
- `POST /api/v1/players` - Create new player
- `GET /api/v1/players/{player_id}` - Get player by ID
- `PUT /api/v1/players/{player_id}` - Update player
- `DELETE /api/v1/players/{player_id}` - Delete player
- `GET /api/v1/players/subteam/{subteam_id}` - Get players by subteam
- `POST /api/v1/players/{player_id}/upload-face` - Upload player face image
- `POST /api/v1/players/face-match` - Match face against players

### Users (Admin only)
- `GET /api/v1/users` - List all users
- `POST /api/v1/users` - Create new user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

## 🎯 Face Recognition

The API includes advanced face recognition capabilities:

### Upload Player Face
```bash
curl -X POST "http://localhost:8000/api/v1/players/1/upload-face" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@player_face.jpg"
```

### Match Face
```bash
curl -X POST "http://localhost:8000/api/v1/players/face-match" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@unknown_face.jpg"
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/tournament
# or for SQLite: DATABASE_URL=sqlite:///./tournament.db

# Redis (optional)
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Uploads
UPLOAD_DIR=uploads
MAX_FILE_SIZE=5242880  # 5MB
```

## 🐳 Docker Deployment

### Build and run with Docker

```bash
# Build the image
docker build -t team-tournament-api .

# Run the container
docker run -p 8000:8000 team-tournament-api
```

### Docker Compose (with Redis and PostgreSQL)

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/tournament
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=tournament
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## 🧪 Testing

### Run tests
```bash
pytest
```

### Manual testing with curl
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "password"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "password"}'
```

## 📊 Performance Features

- **Redis Caching**: Automatic caching of GET requests
- **Database Indexing**: Optimized queries with proper indexes
- **Pagination**: Efficient handling of large datasets
- **File Compression**: Optimized image storage
- **Connection Pooling**: Database connection optimization

## 🔍 Search and Filtering

The API supports advanced search and filtering:

- **Teams**: Search by name
- **Subteams**: Search by name, filter by team
- **Players**: Search by name or email, filter by subteam
- **Pagination**: Limit and offset parameters

## 📈 Data Models

### Team
- `id`: Primary key
- `name`: Team name (unique)
- `description`: Team description
- `coach_name`: Coach name
- `logo_url`: Team logo URL
- `created_at`, `updated_at`: Timestamps

### SubTeam
- `id`: Primary key
- `name`: Subteam name
- `description`: Subteam description
- `team_id`: Foreign key to Team
- `created_at`, `updated_at`: Timestamps

### Player
- `id`: Primary key
- `first_name`, `last_name`: Player name
- `email`: Email (unique)
- `phone`: Phone number
- `date_of_birth`: Date of birth
- `height`, `weight`: Physical attributes
- `position`: Player position
- `jersey_number`: Jersey number
- `is_active`: Active status
- `face_image_url`: Face image URL
- `face_encoding`: Face recognition encoding
- `subteam_id`: Foreign key to SubTeam
- `created_at`, `updated_at`: Timestamps

### User
- `id`: Primary key
- `username`: Username (unique)
- `email`: Email (unique)
- `hashed_password`: Hashed password
- `is_active`: Active status
- `is_superuser`: Superuser status
- `created_at`, `updated_at`: Timestamps

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the logs for debugging information

## 🚀 Deployment

### Production Considerations

1. **Security**:
   - Use strong SECRET_KEY
   - Enable HTTPS
   - Configure CORS properly
   - Use environment variables for secrets

2. **Performance**:
   - Use PostgreSQL for production
   - Configure Redis for caching
   - Set up proper logging
   - Use a production ASGI server (Gunicorn + Uvicorn)

3. **Monitoring**:
   - Set up health checks
   - Monitor database performance
   - Track API usage and errors

4. **Backup**:
   - Regular database backups
   - File upload backups
   - Configuration backups

---

**Built with ❤️ using FastAPI** 