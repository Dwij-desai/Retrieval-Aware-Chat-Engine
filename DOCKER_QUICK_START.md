# 🐳 Docker Quick Start Guide

**Complete guide to running the AI Grocery Chatbot with Docker & Docker Compose**

---

## ✅ **Step 1: Install Docker Desktop**

### macOS Installation

```bash
# Install using Homebrew (easiest)
brew install --cask docker

# Wait for installation to complete, then open Docker app
open /Applications/Docker.app

# Wait 45-60 seconds for Docker daemon to start
sleep 45

# Verify installation
docker --version
docker-compose --version
```

**Expected output:**
```
Docker version 24.0.0 (or higher)
docker-compose version 2.18.0 (or higher)
```

---

## 🔧 **Step 2: Configure Environment**

Your `.env` file already exists. Verify it has API keys:

```bash
cat /Volumes/MacDisk_1TB/AI_SAAS\(ChatBot\)\ copy/.env
```

**Must contain:**
```
GOOGLE_API_KEY=your_key_or_empty
GROQ_API_KEY=your_actual_key_here
LLM_PROVIDER=groq
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

If you need to add/update keys:
```bash
cat > .env << EOF
GOOGLE_API_KEY=
GROQ_API_KEY=your_groq_key_here
LLM_PROVIDER=groq
CHUNK_SIZE=500
CHUNK_OVERLAP=50
EOF
```

---

## 🚀 **Step 3: Start All Services with Docker Compose**

```bash
# Navigate to project
cd /Volumes/MacDisk_1TB/AI_SAAS\(ChatBot\)\ copy

# Start all services (API + ChromaDB + Frontend)
docker-compose up -d

# Check status
docker-compose ps
```

**Expected output:**
```
NAME                COMMAND                 STATUS
ai-chatbot-api      "uvicorn backend.a…"   Up 30 seconds
ai-chatbot-chroma   "python -m chromadb…"  Up 35 seconds
```

---

## ✨ **Services Running**

| Service | URL | Purpose |
|---------|-----|---------|
| **Backend API** | http://localhost:8000 | REST API for chatbot |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **ChromaDB** | http://localhost:8001 | Vector database |
| **Frontend** | http://localhost:5173 | React chat UI |

---

## 🧪 **Step 4: Test Services**

### Test API Health
```bash
# Check if API is running
curl http://localhost:8000/health

# Expected response: 200 OK
```

### Test ChromaDB
```bash
# Check vector database
curl http://localhost:8001/api/v1

# Should return database info
```

### Test in Browser
```bash
# Open frontend
open http://localhost:5173

# Open API docs
open http://localhost:8000/docs
```

---

## 📚 **Step 5: Ask Questions**

In the frontend (http://localhost:5173), try these:

```
"What dairy products do you have?"
"Do you have salmon?"
"What products cost under $5?"
"What spices do you carry?"
"How much is chicken breast?"
```

---

## 📊 **Viewing Logs**

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f chroma

# View last 50 lines
docker-compose logs --tail 50 api
```

---

## 🛑 **Stop Services**

```bash
# Stop all services (keep volumes)
docker-compose down

# Stop and remove everything (including data)
docker-compose down -v
```

---

## 🔄 **Restart Services**

```bash
# Restart after code changes
docker-compose restart

# Full restart (down then up)
docker-compose down
docker-compose up -d
```

---

## 📁 **File Structure**

```
Project Root/
├── Dockerfile              # API container definition
├── docker-compose.yml      # Service orchestration
├── .env                    # Environment variables
├── backend/                # Python FastAPI code
│   ├── api.py             # Main API endpoints
│   ├── config.py          # Configuration
│   ├── rag_engine.py      # RAG logic
│   └── ...
├── frontend/              # React frontend
│   ├── src/
│   ├── package.json
│   └── ...
├── data/                  # Documents to ingest
│   ├── grocery_store_inventory.csv
│   ├── grocery_catalog.json
│   └── grocery_store_guide.txt
└── chroma_db/             # Vector database (auto-created)
```

---

## 🆘 **Troubleshooting**

### Docker daemon not running
```bash
# Start Docker desktop app
open /Applications/Docker.app

# Or check Docker status
docker ps
```

### Port already in use (8000, 8001, 5173)
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
```

### Services not starting
```bash
# Check logs
docker-compose logs api

# Rebuild images
docker-compose build

# Start fresh
docker-compose up -d
```

### API returning errors
```bash
# Check if ChromaDB is connected
curl http://localhost:8001/api/v1

# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api
```

### Need to clear database
```bash
# Stop services
docker-compose down

# Remove volume
docker volume rm ai-saas-chatbot_chroma_storage

# Start fresh
docker-compose up -d
```

---

## 📈 **Advanced: Rebuild After Code Changes**

```bash
# Rebuild API image after code changes
docker-compose build api

# Restart service
docker-compose up -d

# Or in one command
docker-compose up -d --build
```

---

## 🌐 **Docker Networking**

Services communicate internally:
- API → ChromaDB: `http://chroma:8000` (inside Docker)
- API → External: `http://localhost:8001` (from host)

---

## 💾 **Persistent Data**

Your data persists in Docker volumes:
- ChromaDB data: `ai-saas-chatbot_chroma_storage`
- Check volumes: `docker volume ls`

---

## 📝 **Common Commands**

```bash
# View services
docker-compose ps

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec api bash
docker-compose exec api python backend/ingest.py

# Check container stats
docker stats

# Remove all stopped containers
docker container prune

# List images
docker images
```

---

## ✅ **Verification Checklist**

After starting services:

- [ ] `docker-compose ps` shows 2 running services
- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `curl http://localhost:8001/api/v1` returns data
- [ ] Frontend loads at http://localhost:5173
- [ ] API docs at http://localhost:8000/docs
- [ ] Chatbot responds to questions
- [ ] No errors in `docker-compose logs`

---

## 🎯 **Quick Commands Summary**

```bash
# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop everything
docker-compose down

# Restart services
docker-compose restart

# Full cleanup
docker-compose down -v
```

---

**You're all set! 🚀**

Your AI Grocery Store Chatbot is now running in Docker with:
- ✅ Isolated, reproducible environment
- ✅ Production-ready setup
- ✅ Easy to deploy anywhere
- ✅ Fast startup/shutdown

**Next steps:**
1. Open http://localhost:5173
2. Ask: "What grocery items do you have?"
3. Enjoy! 🎉
