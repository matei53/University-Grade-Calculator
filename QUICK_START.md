# Quick Start Guide - Server Backend

## TL;DR - Get Running in 5 Minutes

### Prerequisites
- PostgreSQL installed (https://www.postgresql.org/download/)
- Python 3.9+

### Step 1: Create Database
```bash
psql -U postgres
CREATE DATABASE unigrades_db;
\q
```

### Step 2: Configure Environment
Copy and edit `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL password:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/unigrades_db
SECRET_KEY=your-secret-key
```

### Step 3: Install & Run Server
```bash
cd server
pip install -r requirements.txt
python main.py
```

You should see: `INFO: Uvicorn running on http://0.0.0.0:8000`

### Step 4: Run Client (New Terminal)
```bash
python main.py
```

## Key Differences from Old Setup

| Aspect | Before | After |
|--------|--------|-------|
| Database | SQLite (local file) | PostgreSQL (networked) |
| Deployment | Single process | Client-Server architecture |
| Multi-user | ❌ Not possible | ✅ Full support |
| Port | N/A | 8000 |
| Authentication | Session-based | JWT tokens |

## Troubleshooting

**"Cannot connect to the API server"**
- Make sure server is running in another terminal
- Check PostgreSQL is running

**"FATAL: role 'postgres' does not exist"**
```bash
createuser -s postgres
```

**"Database 'unigrades_db' does not exist"**
```bash
psql -U postgres -c "CREATE DATABASE unigrades_db;"
```

**Port 8000 already in use**
```bash
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Mac/Linux
# Then kill the process or use different port
```

## Testing the API

Visit http://localhost:8000/docs for interactive API documentation.

## What Changed in Code

1. **Database Access**: Now goes through HTTP API instead of direct SQLite connection
2. **Services**: Updated to use `APIClient` instead of repositories
3. **Authentication**: JWT tokens instead of session-based
4. **Configuration**: `.env` file instead of hardcoded paths

## Next: Production Deployment

See full `SERVER_SETUP.md` for:
- Detailed PostgreSQL setup
- Docker deployment
- Cloud deployment (AWS, Heroku)
- HTTPS/SSL setup
- Gunicorn/process managers
