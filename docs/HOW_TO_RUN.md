# How to Run the AI SaaS Chatbot

This guide covers all the ways to run the project - from quick Docker setup to local development.

## ⚡ Quick Start (5 minutes with Docker)

### Prerequisites
- Docker & Docker Compose installed
  ```bash
  docker --version
  docker-compose --version
  ```
- API keys (see setup section below)

### 1. Set Up Environment
```bash
# Go to project directory
cd /Volumes/MacDisk_1TB/AI_SAAS\(ChatBot\)\ copy

# Copy .env template if needed
cp .env.example .env  # (optional, .env already exists)

# Edit .env with your API keys
export GOOGLE_API_KEY=your_key_here
export GROQ_API_KEY=your_key_here
```

### 2. Validate Docker Setup
```bash
bash scripts/validate-docker.sh
```

**Expected output:**
```
✓ Dockerfile found
✓ docker-compose.yml found
✓ .dockerignore found
✓ requirements.txt found
✓ YAML structure looks valid
✓ ChromaDB service defined
✓ API service defined
✓ Service dependencies defined
✓ GOOGLE_API_KEY present

✅ All Docker files validated successfully!
```

### 3. Start Services
```bash
docker-compose up -d
```

**What gets started:**
- ✅ FastAPI backend (port 8000)
- ✅ ChromaDB vector database (port 8001)

### 4. Check Services are Running
```bash
docker-compose ps
```

**Expected output:**
```
NAME                COMMAND                 STATUS
ai-chatbot-api      "uvicorn backend.a…"   Up 10 seconds
ai-chatbot-chroma   "python -m chromadb…"  Up 20 seconds
```

### 5. Test the API
```bash
# Health check
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this chatbot?",
    "chat_id": "test-session"
  }'
```

**Expected response:**
```json
{
  "answer": "This is a Retrieval-Augmented Generation (RAG) system...",
  "latency_ms": 450.23,
  "chat_id": "test-session"
}
```

### 6. View Logs (if needed)
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f chroma
```

### 7. Stop Services
```bash
docker-compose down

# Remove volumes (data) too
docker-compose down -v
```

---

## 🖥️ Local Development Setup

For development without Docker:

### Prerequisites
- Miniconda/Conda installed
- Python 3.11+
- API keys (Groq and/or Google Gemini)

### 1. Create Conda Environment
```bash
# Option A: Run setup script (automatic)
bash scripts/Environment.sh

# Option B: Manual setup
conda env create -f environment.yml
conda activate ai_saas
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Create .env file
cat > .env << EOF
GOOGLE_API_KEY=your_google_key
GROQ_API_KEY=your_groq_key
PROVIDER=groq
LLM_PROVIDER=groq
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
EOF
```

### 3. Ingest Data (First Time Only)
```bash
# Activate environment
conda activate ai_saas

# Ingest documents from data/ folder
python backend/ingest.py
```

**What happens:**
- Scans `data/` folder for PDF, CSV, JSON, Excel, TXT files
- Splits documents into chunks
- Generates embeddings
- Stores in ChromaDB (`chroma_db/` folder)

### 4. Start API Server
```bash
# Activate environment
conda activate ai_saas

# Start server (recommended)
bash scripts/start.sh

# OR start manually with uvicorn
uvicorn backend.api:app --reload --port 8000 --host 0.0.0.0
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 5. Test the API
```bash
# In another terminal
curl http://localhost:8000/health

# View interactive API docs
open http://localhost:8000/docs
```

### 6. Stop Server
```bash
# Press Ctrl+C in the terminal
```

---

## 🔧 Advanced: Enable Observability & Evaluation

### Enable LangSmith Tracing
```bash
# Set your LangSmith API key
export LANGCHAIN_API_KEY=your_langsmith_key

# Start the server
bash scripts/start.sh
# or docker-compose up -d

# All RAG operations are now traced
# View at: https://smith.langchain.com/projects/ai-saas-chatbot
```

### Run Evaluation
```bash
# Evaluate RAG quality on golden dataset
python backend/evaluation.py
```

**Output:**
```
📊 Evaluation Results:
  faithfulness: 0.847
  answer_relevancy: 0.821
  context_precision: 0.903
  context_recall: 0.756
  aggregate_score: 0.832

✅ Evaluation report saved to evaluation_report.json
```

### Auto-Ingest Files
```bash
# Watch data/ folder for new files (real-time)
python backend/ingest_orchestrator.py --mode watch

# Or schedule periodic ingestion
python backend/ingest_orchestrator.py --mode schedule --interval daily

# Or one-time ingestion
python backend/ingest_orchestrator.py --mode once
```

---

## 🧪 Run Tests

### Quick Test Run
```bash
# All tests
pytest

# With coverage report
pytest --cov=backend --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Fast tests (exclude slow)
pytest -m "not slow"

# Verbose output
pytest -vv

# Stop on first failure
pytest -x
```

### Use Test Runner Script
```bash
# All tests
bash scripts/test.sh

# Unit tests
bash scripts/test.sh unit

# Coverage report
bash scripts/test.sh coverage

# Watch mode (auto re-run)
bash scripts/test.sh watch

# Parallel execution
bash scripts/test.sh parallel
```

---

## 🐳 Docker Detailed Usage

### View Service Logs
```bash
# Real-time logs for API
docker-compose logs -f api

# Last 50 lines of API logs
docker-compose logs --tail 50 api

# View ChromaDB logs
docker-compose logs -f chroma
```

### Execute Commands in Container
```bash
# Run Python script
docker-compose exec api python backend/evaluation.py

# Run tests in container
docker-compose exec api pytest

# Start bash shell
docker-compose exec api bash
```

### Rebuild Docker Image
```bash
# After code changes
docker-compose build

# Then restart
docker-compose up -d
```

### Check Service Health
```bash
# API health
curl http://localhost:8000/health

# ChromaDB health
curl http://localhost:8001/api/v1

# View both in one go
curl http://localhost:8000/health && curl http://localhost:8001/api/v1
```

---

## 📍 API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

### Ask Question
```bash
POST http://localhost:8000/ask

Request:
{
  "question": "What is this system?",
  "chat_id": "user_123"
}

Response:
{
  "answer": "This is a RAG-based chatbot...",
  "latency_ms": 450.2,
  "chat_id": "user_123"
}
```

### API Documentation
```
Interactive Docs: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
OpenAPI Schema: http://localhost:8000/openapi.json
```

---

## 📂 File Locations

```
Project Root: /Volumes/MacDisk_1TB/AI_SAAS(ChatBot) copy

Key Directories:
├── backend/              # Python source code
├── data/                 # Input documents for ingestion
├── chroma_db/            # Vector database (auto-created)
├── tests/                # Pytest test suite
├── docs/                 # Documentation
├── scripts/              # Bash scripts
│   ├── start.sh         # Start API server
│   ├── Environment.sh   # Setup conda env
│   ├── test.sh          # Run tests
│   └── validate-docker.sh # Validate Docker setup
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Service orchestration
├── requirements.txt     # Python dependencies
├── environment.yml      # Conda environment
├── pytest.ini          # Pytest configuration
└── .env                # Environment variables (your keys)
```

---

## 🆘 Troubleshooting

### Docker Issues

**Docker daemon not running:**
```bash
# Mac
open /Applications/Docker.app

# Linux
sudo systemctl start docker
```

**Port 8000 already in use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change docker-compose.yml port mapping
```

**ChromaDB connection refused:**
```bash
# Check if ChromaDB is running
docker-compose ps

# View ChromaDB logs
docker-compose logs chroma

# Restart services
docker-compose down
docker-compose up -d
```

### Local Development Issues

**Module not found errors:**
```bash
# Ensure environment is activated
conda activate ai_saas

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Try again
python backend/ingest.py
```

**API keys not recognized:**
```bash
# Check .env file
cat .env

# Verify variables are set
echo $GOOGLE_API_KEY
echo $GROQ_API_KEY

# Re-source .env if needed
source .env
```

**Tests failing:**
```bash
# Run with verbose output
pytest -vv

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

---

## 📊 Monitoring & Debugging

### View API Metrics
```bash
# Check health
curl http://localhost:8000/health

# View interactive docs with try-it-out
open http://localhost:8000/docs
```

### Check Vector Database
```bash
# ChromaDB status
curl http://localhost:8001/api/v1

# Should return collection info
```

### View Evaluation Results
```bash
# After running evaluation
cat evaluation_report.json

# Pretty print
python -m json.tool evaluation_report.json
```

### Check Chat History
```bash
# View SQLite chat memory
sqlite3 chat_memory.db "SELECT * FROM chat_messages LIMIT 10;"
```

---

## 🎯 Common Workflows

### Workflow 1: First Run (Docker)
```bash
cd /Volumes/MacDisk_1TB/AI_SAAS\(ChatBot\)\ copy
bash scripts/validate-docker.sh
docker-compose up -d
curl http://localhost:8000/health
open http://localhost:8000/docs
```

### Workflow 2: Development with Tests
```bash
conda activate ai_saas
bash scripts/test.sh coverage  # Run tests with coverage
bash scripts/start.sh          # Start server
# Make code changes
pytest                         # Re-run tests
```

### Workflow 3: Evaluate Model Quality
```bash
# Setup
docker-compose up -d
export LANGCHAIN_API_KEY=your_key

# Evaluate
python backend/evaluation.py

# View results
cat evaluation_report.json
```

### Workflow 4: Ingest New Data
```bash
# Place files in data/ folder
cp /path/to/docs/* data/

# Method 1: Manual
docker-compose exec api python backend/ingest.py

# Method 2: Automatic
python backend/ingest_orchestrator.py --mode watch
# Files will be auto-ingested as they arrive
```

### Workflow 5: Debug a Failed Query
```bash
# Enable LangSmith tracing
export LANGCHAIN_API_KEY=your_key

# Start server
docker-compose up -d

# Make a query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "chat_id": "debug"}'

# View trace in LangSmith dashboard
open https://smith.langchain.com/projects/ai-saas-chatbot
```

---

## 📚 Documentation References

| Topic | File |
|-------|------|
| Docker Setup | `docs/DOCKER_SETUP.md` |
| Evaluation Framework | `docs/EVALUATION.md` |
| Observability | `docs/LANGSMITH.md` |
| Auto Ingestion | `docs/AUTO_INGEST.md` |
| Testing | `docs/TESTING.md` |
| MLOps Summary | `docs/MLOPS_SUMMARY.md` |
| Technical Details | `docs/explanation.md` |
| Architecture | `README.md` |

---

## ✅ Verification Checklist

After running the project:

- [ ] `docker-compose ps` shows 2 running services (api, chroma)
- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `curl http://localhost:8001/api/v1` returns ChromaDB info
- [ ] API docs accessible at `http://localhost:8000/docs`
- [ ] Sample question returns an answer
- [ ] `pytest` runs without errors
- [ ] Evaluation runs and generates report
- [ ] LangSmith shows traces (if API key set)

---

**You're all set! Start with the Quick Start section above and you'll be running in 5 minutes.** 🚀
