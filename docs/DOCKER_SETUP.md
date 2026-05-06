# Step-1: Docker Setup Guide

## Overview
This guide walks you through containerizing the AI SaaS Chatbot using Docker and docker-compose.

## What Was Created

### 1. **Dockerfile**
- Multi-stage build for optimized image size
- Python 3.11-slim base image
- Installs all dependencies from `requirements.txt`
- Exposes port 8000
- Includes health check
- Sets `PYTHONUNBUFFERED=1` for real-time logs

### 2. **docker-compose.yml**
Orchestrates two services:

#### Service: `chroma`
- **Image:** chromadb/chroma:latest
- **Port:** 8001:8000 (avoid port 8000 conflict)
- **Volume:** Named volume `chroma_data` for persistence
- **Environment:** `IS_PERSISTENT=true`, `PERSIST_DIRECTORY=/data`
- **Health Check:** Verifies ChromaDB API is responding
- **Network:** Isolated network `ai-chatbot-network`

#### Service: `api`
- **Build:** Builds from local Dockerfile
- **Port:** 8000:8000 (main API port)
- **Environment:** Loads from `.env` (see below)
- **Volumes:**
  - Backend code (for live reload during dev)
  - Data directory
  - ChromaDB data persistence
  - Chat memory database
- **Depends On:** Waits for ChromaDB to be healthy before starting
- **Health Check:** Monitors API responsiveness

### 3. **.dockerignore**
Excludes unnecessary files from Docker build context:
- Git files
- Python cache
- IDE configs
- Large datasets
- Documentation

## Prerequisites

1. **Docker & Docker Compose** installed
   ```bash
   docker --version
   docker-compose --version
   ```

2. **API Keys** in `.env` file
   ```
   GOOGLE_API_KEY=your-google-api-key
   GROQ_API_KEY=your-groq-api-key  # Optional
   PROVIDER=groq  # or "gemini"
   ```

## Usage

### Build the Docker Image
```bash
docker-compose build
```

### Start Services
```bash
docker-compose up -d
```

This will:
1. Start ChromaDB on port 8001
2. Wait for ChromaDB to be healthy
3. Start FastAPI on port 8000
4. Mount local volumes for development

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f chroma
```

### Stop Services
```bash
docker-compose down
```

### Remove Everything (including data)
```bash
docker-compose down -v  # -v removes volumes
```

## Environment Variables

Create or update `.env` in the project root:

```env
# Required
GOOGLE_API_KEY=sk-...

# Optional
GROQ_API_KEY=gsk-...
PROVIDER=groq
```

The `docker-compose.yml` will automatically load these into the containers.

## API Access

Once running:
- **API Base URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ChromaDB:** http://localhost:8001/api/v1

## Testing the Setup

### Test API Health
```bash
curl http://localhost:8000/health
```

### Test ChromaDB
```bash
curl http://localhost:8001/api/v1
```

### Test Full RAG Pipeline
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this chatbot?",
    "session_id": "test-session"
  }'
```

## Development Workflow

Since backend code is volume-mounted, changes will auto-reflect without rebuilding:

1. Edit `backend/*.py`
2. API automatically reloads (uvicorn `--reload`)
3. Test at http://localhost:8000/docs

## Production Considerations

For production deployment:
1. Remove `--reload` flag from uvicorn command
2. Use external PostgreSQL instead of SQLite for `chat_memory.db`
3. Use managed vector DB (Qdrant Cloud, Weaviate Cloud)
4. Add resource limits to services
5. Use a reverse proxy (Nginx) for load balancing
6. Enable HTTPS/TLS

## Troubleshooting

### Port 8000 already in use
```bash
# Find process using port 8000
lsof -i :8000
# Kill it or change docker-compose.yml port mapping
```

### ChromaDB connection refused
- Check ChromaDB logs: `docker-compose logs chroma`
- Ensure ChromaDB is healthy: `docker-compose ps`
- Verify health check passes

### API can't connect to ChromaDB
- Services must be on same network (already configured)
- Use service name `chroma` as hostname (already configured)

### Out of disk space
```bash
docker system prune -a  # Remove unused images
docker volume prune     # Remove unused volumes
```

## Next Steps

1. ✅ **Docker Setup Complete**
2. 📊 Implement Ragas evaluation (Step-2)
3. 🔍 Add LangSmith tracing (Step-3)
4. 🤖 Automate data ingestion (Step-4)
5. ✔️ Expand pytest coverage (Step-5)
