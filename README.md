# AI SaaS Chatbot — RAG Engine

A professional Retrieval-Augmented Generation (RAG) system for AI SaaS applications. This backend uses a high-performance, multi-provider LLM stack with local vector storage and persistent conversation memory.

## 🚀 Key Features

- **Multi-Provider LLM Support**: Seamlessly switch between **Groq** (ultra-fast) and **Google Gemini** via environment variables.
- **Smart Data Ingestion**: Supports PDF, TXT, CSV, Excel (`.xlsx`), and JSON.
- **Local Embeddings**: Uses `BAAI/bge-small-en-v1.5` locally (via HuggingFace) for free, private, and fast vector generation.
- **Vector Database**: Persistent local storage using **ChromaDB**.
- **Persistent Chat Memory**: Conversations are stored in a local SQLite database, allowing for multi-turn follow-up questions.
- **Automated Fallbacks**: Automatically retries with alternative models if the primary provider hits a quota limit or is unavailable.
- **Performance Optimized**: Server-side pre-warming reduces first-request latency from ~10s to <1s.

## 📁 Project Structure

```text
.
├── backend/            # Core Python modules
│   ├── api.py          # FastAPI HTTP layer & Endpoints
│   ├── config.py       # Pydantic Settings & Provider routing
│   ├── embedder.py     # Embedding model configuration
│   ├── ingest.py       # Data loading & chunking pipeline
│   ├── memory.py       # SQLite persistent chat history
│   ├── rag_engine.py   # RAG logic & LLM chain
│   └── vector_store.py # ChromaDB management
├── data/               # Source documents for ingestion
├── docs/               # Technical documentation & guides
├── scripts/            # Setup and execution scripts
├── .env.example        # Template for environment variables
├── environment.yml     # Conda environment definition
└── GEMINI.md           # Project-specific guidelines
```

## 🛠️ Setup & Installation

### Option 1: Docker (Recommended for Production)
The easiest way to run the entire system with consistent environments:

```bash
# Validate setup
bash scripts/validate-docker.sh

# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

**Services Started:**
- **API**: http://localhost:8000 (with docs at /docs)
- **ChromaDB**: http://localhost:8001/api/v1

See `docs/DOCKER_SETUP.md` for detailed Docker configuration and troubleshooting.

### Option 2: Local Development
For development or systems without Docker:

#### Prerequisites
- [Conda](https://docs.conda.io/en/latest/miniconda.html) or [Miniconda](https://docs.anaconda.com/free/miniconda/index.html)
- API Keys for [Groq](https://console.groq.com) or [Google AI Studio](https://aistudio.google.com)

#### Environment Setup
Run the setup script to create the `ai_saas` conda environment and install dependencies:

```bash
bash scripts/Environment.sh
```

### Configuration
Create a `.env` file in the project root:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_gemini_key_here

# Optional overrides
MEMORY_MAX_MESSAGES=6
```

## 🏃 Usage

### With Docker (Recommended)
```bash
docker-compose up -d
```

Then test the API:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

### Local Development

#### 1. Ingest Data
Place your documents in the `data/` folder and run the ingestion pipeline:

```bash
conda activate ai_saas
python backend/ingest.py
```

#### 2. Start the API Server
The easiest way to start the server with all paths correctly set is using the start script:

```bash
bash scripts/start.sh
```

The API will be available at:
- **API Base**: `http://127.0.0.1:8000`
- **Interactive Docs (Swagger)**: `http://127.0.0.1:8000/docs`

## 🔌 API Endpoints

### `POST /ask`
Submit a question to the chatbot.

**Request Body:**
```json
{
  "question": "What pricing plans are available?",
  "chat_id": "user_123"
}
```

**Success Response:**
```json
{
  "answer": "We offer Basic, Pro, and Enterprise plans...",
  "latency_ms": 450.2,
  "chat_id": "user_123"
}
```

## 📝 Roadmap
- [x] Docker containerization for easy deployment
- [ ] Next.js Frontend UI for browser interaction
- [ ] API-based ingestion endpoint
- [ ] Multi-user authentication support
- [ ] Ragas evaluation framework for performance metrics
- [ ] LangSmith tracing for observability
- [ ] Automated data ingestion pipeline

## 📄 License
This project is licensed under the MIT License.
