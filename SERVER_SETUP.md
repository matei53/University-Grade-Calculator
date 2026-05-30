# Server Backend Setup Guide

This document explains how to set up and run the UniGrade backend server using FastAPI and PostgreSQL.

## Architecture Overview

The project has been refactored from a single-process SQLite application to a **multi-user client-server architecture**:

- **Backend Server**: FastAPI application running on `localhost:8000` (or any configured host)
- **Database**: PostgreSQL (replaces SQLite for multi-user support)
- **Frontend**: PyQt6 desktop client that communicates via HTTP REST API
- **Authentication**: JWT tokens for secure API access

## Prerequisites

### System Requirements
- Python 3.9 or higher
- PostgreSQL 12 or higher (for production, or use below for local development)

### Install PostgreSQL

**Windows:**
1. Download from https://www.postgresql.org/download/windows/
2. Run the installer and remember the password you set for the `postgres` user
3. PostgreSQL will typically install on port 5432

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Setup Instructions

### 1. Install Server Dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Create PostgreSQL Database

Open a terminal and connect to PostgreSQL:

```bash
# Windows/macOS/Linux
psql -U postgres
```

When prompted, enter the password you set during PostgreSQL installation.

Then run:

```sql
CREATE DATABASE unigrades_db;
\q
```

### 3. Configure Environment Variables

Update `.env` with your PostgreSQL credentials:
(I think this is what you have to do, this is the guide the AI gave me when I made this)

```
# PostgreSQL connection
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/unigrades_db

# JWT Secret key - change this in production!
SECRET_KEY=your-super-secret-key-change-this-in-production

# Server settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### 4. Initialize the Database

The database tables will be created automatically when the server starts. The universities and majors will be seeded from `data/universities.json` and `data/majors.json`.

### 5. Run the Server

From the project root directory:

```bash
# Option 1: Run directly with Python
cd server
python main.py

# Option 2: Run with uvicorn (better for development)
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6. Verify Server is Running

Visit in your browser:
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Docs Alternative**: http://localhost:8000/redoc

### 7. Run the PyQt6 Client

In a **separate terminal**, from the project root:

```bash
python main.py
```

The client will automatically connect to the server on startup.

## API Endpoints Reference

All endpoints require an `Authorization: Bearer {token}` header (except auth endpoints).

### Authentication

```
POST /auth/register
POST /auth/login
POST /auth/verify-token
```

### Profile

```
GET  /profile                    # Get user profile
PUT  /profile                    # Update profile (university_id, major_id)
GET  /profile/universities       # List all universities
GET  /profile/majors            # List all majors
```

### Subjects

```
POST /subjects                  # Add a subject
GET  /subjects/years           # Get user's academic years with subjects
```

### Assessments

```
POST /assessments/{subject_id}  # Add assessment to a subject
```

## Troubleshooting

### "Cannot connect to the API server"

**Problem**: The PyQt6 client shows this error on startup.

**Solution**:
1. Make sure the server is running: `python server/main.py`
2. Check that PostgreSQL is running
3. Verify `.env` file has correct `DATABASE_URL`

### "FATAL: role 'postgres' does not exist"

**Solution**:
```bash
# Create the postgres user (PostgreSQL may require this on some systems)
createuser -s postgres
```

### "psql: error: connection refused"

**Solution**:
- PostgreSQL is not running
- Start it with: `pg_ctl start` or `brew services start postgresql`

### "Database 'unigrades_db' does not exist"

**Solution**:
```bash
psql -U postgres -c "CREATE DATABASE unigrades_db;"
```

### Port 8000 is already in use

**Solution**:
```bash
# Use a different port
uvicorn server.main:app --reload --port 8001

# Update .env if needed
SERVER_PORT=8001
```

## Development Tips

### Watch Mode
Use `--reload` flag with uvicorn for automatic server restart on code changes:

```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Inspection

```bash
# Connect to database
psql -U postgres -d unigrades_db

# List tables
\dt

# Check users table
SELECT * FROM users;

# Exit
\q
```

### Clear Database (Development Only)

If you need to reset the database:

```bash
# Remove all data (keeps schema)
psql -U postgres -d unigrades_db -f /dev/stdin << 'EOF'
TRUNCATE users CASCADE;
EOF

# Or drop and recreate database
psql -U postgres -c "DROP DATABASE unigrades_db;"
psql -U postgres -c "CREATE DATABASE unigrades_db;"
```

Then restart the server to reinitialize.

## Deployment (Production)

For production deployment:

1. **Use a proper WSGI server** (not just uvicorn):
   ```bash
   pip install gunicorn
   gunicorn server.main:app -w 4 -b 0.0.0.0:8000
   ```

2. **Change SECRET_KEY** in `.env` to a strong random string

3. **Use environment-specific database**:
   ```
   DATABASE_URL=postgresql://prod_user:strong_password@prod_server:5432/unigrades_prod
   ```

4. **Enable HTTPS/SSL** with a reverse proxy (nginx, Apache)

5. **Use a process manager** (systemd, supervisord)

6. **Configure CORS** properly in `server/main.py` if client is on different domain

## Architecture Details

### Request Flow

```
PyQt6 Client
    ↓ (HTTP with JWT token)
FastAPI Server (server/main.py)
    ↓ (SQLAlchemy ORM)
PostgreSQL Database
```

### File Structure

```
server/
├── main.py              # FastAPI app entry point
├── config.py           # Configuration (DB URL, JWT secret)
├── database.py         # SQLAlchemy setup
├── models.py           # ORM models (User, Subject, etc.)
├── schemas.py          # Pydantic request/response schemas
├── dependencies.py     # Dependency injection (auth)
├── requirements.txt    # Python dependencies
├── routers/
│   ├── auth.py        # /auth endpoints
│   ├── profile.py     # /profile endpoints
│   ├── subjects.py    # /subjects endpoints
│   └── assessments.py # /assessments endpoints
└── services/
    ├── auth_service.py
    ├── subject_service.py
    └── __init__.py

client/
└── api_client.py      # HTTP client for PyQt6 app

ui/
├── app.py            # PyQt6 router (no DB changes)
├── screens/
│   ├── login_screen.py     # Uses API client
│   ├── signup_screen.py    # Uses API client
│   ├── dashboard_screen.py # Uses API client
│   └── subject_screen.py   # Uses API client
└── components/       # UI components (unchanged)

services/
├── auth_service.py      # Now uses API client
├── dashboard_service.py # Now uses API client
├── data_service.py      # Now uses API client
└── grade_service.py     # Pure calculation (unchanged)
```

## Next Steps

1. ✅ Set up PostgreSQL
2. ✅ Install server dependencies
3. ✅ Configure `.env`
4. ✅ Run the server
5. ✅ Run the PyQt6 client
6. Test user registration and login
7. Add subjects and assessments
8. Deploy to production when ready

## Support

For issues or questions, check:
- Server logs: Look at FastAPI output for errors
- Database logs: Check PostgreSQL logs
- API Documentation: Visit http://localhost:8000/docs
