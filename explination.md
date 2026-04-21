# AI SaaS Chatbot - Project Documentation

This document summarizes the system architecture, component functionality, and provides the current code implementation for the AI SaaS Chatbot backend.

---

## 1. System Configuration (`backend/config.py`)
The `config.py` file serves as the centralized settings management hub using **Pydantic**.

### Key Responsibilities:
*   **Environment Variables**: Automatically loads secrets (like `GOOGLE_API_KEY`) from `.env` and `.gitignore/.env`.
*   **Vector Database Settings**: Defines the storage path (`./chroma_db`) and collection name for ChromaDB.
*   **RAG Parameters**:
    *   `chunk_size` (500) & `chunk_overlap` (50): Controls how documents are split for the LLM.
    *   `top_k` (4): Determines how many relevant context snippets are retrieved per query.
*   **LLM Configuration**: Targets `gemini-1.5-flash` with a low `temperature` (0.1) to ensure factual, deterministic responses.

### Source Code:
```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google Gemini API key (free tier available)
    google_api_key: str

    # Vector DB
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "ai_saas_docs"

    # Retrieval
    top_k: int = 4  # how many chunks to retrieve
    chunk_size: int = 500  # characters per chunk
    chunk_overlap: int = 50  # overlap between chunks

    # LLM — Gemini 1.5 Flash is free tier, fast, and capable
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.1

    class Config:
        env_file = (".env", ".gitignore/.env")


settings = Settings()
```

---

## 2. Data Ingestion Pipeline (`backend/ingest.py`)
The ingestion layer transforms raw data into a format searchable by the AI.

### Key Functions:
*   **`load_documents`**: Scans the data directory and loads various file types into LangChain Document objects. Supports PDF, TXT, CSV, Excel, and JSON.
*   **`chunk_documents`**: Uses the `RecursiveCharacterTextSplitter` to break long texts into smaller chunks. It prioritizes splitting at paragraphs and sentences to maintain context integrity.

### Source Code:
```python
import os
import json

from config import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    CSVLoader,
)
from langchain_core.documents import Document
import pandas as pd


def load_documents(data_dir: str) -> list:
    """Load PDFs, text, CSV, Excel, and JSON files from a directory."""
    documents = []

    # Load files
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)

        if filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
            documents.extend(loader.load())

        elif filename.endswith(".txt"):
            loader = TextLoader(filepath)
            documents.extend(loader.load())

        elif filename.endswith(".csv"):
            loader = CSVLoader(filepath)
            documents.extend(loader.load())

        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            # Load Excel using pandas and convert to LangChain Documents
            df = pd.read_excel(filepath)
            # Convert each row to a string or a structured format
            for index, row in df.iterrows():
                content = " ".join([f"{col}: {val}" for col, val in row.items()])
                doc = Document(
                    page_content=content,
                    metadata={"source": filepath, "row": index}
                )
                documents.append(doc)

        elif filename.endswith(".json"):
            with open(filepath, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            if isinstance(json_data, list):
                for index, item in enumerate(json_data):
                    documents.append(
                        Document(
                            page_content=json.dumps(item),
                            metadata={"source": filepath, "item": index}
                        )
                    )
            else:
                documents.append(
                    Document(
                        page_content=json.dumps(json_data),
                        metadata={"source": filepath}
                    )
                )

    print(f"Loaded {len(documents)} total documents/rows from {data_dir}")
    return documents


def chunk_documents(documents: list) -> list:
    """
    Split documents into chunks.

    WHY RecursiveCharacterTextSplitter?
    - Tries to split at natural boundaries: paragraph → sentence → word
    - Smarter than splitting at exactly 500 chars (avoids cutting mid-sentence)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,  # 500 chars
        chunk_overlap=settings.chunk_overlap,  # 50 char overlap
        separators=["\n\n", "\n", ". ", " ", ""],  # priority order
    )

    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")
    return chunks


# Quick test
if __name__ == "__main__":
    docs = load_documents("./data")
    chunks = chunk_documents(docs)
    print(f"First chunk:\n{chunks[0].page_content}")
```

---

## 3. Recent Updates: Multi-Format Support
We have expanded the ingestion capabilities beyond simple Text and PDF files.

### Added CSV Support
*   Implemented using LangChain's `CSVLoader`.
*   Each row in a CSV file is treated as a distinct document, allowing for granular data retrieval.

### Added Excel Support (`.xlsx`, `.xls`)
*   Integrated `pandas` and `openpyxl` for robust Excel processing.
*   **Structured Conversion**: Every row is converted into a string format: `ColumnName: Value`, ensuring the LLM understands the tabular context during retrieval.

### Added JSON Support (`.json`)
*   Implemented using Python's built-in `json` module.
*   **Flexible Handling**:
    *   If the root JSON is an array, each element is stored as a separate document (`item` index in metadata).
    *   If the root JSON is an object/value, the full payload is stored as one document.

---

## 4. Environment & Dependencies
To support the new formats, the following updates were made:
*   **`requirements.txt`**: Added `pandas` and `openpyxl`.
*   **JSON Parsing**: Uses Python's built-in `json` module (no extra dependency required).
*   **Compatibility Fix**: Loosened `grpcio-status` version requirements to resolve dependency conflicts found in Python 3.14 environments.

---

## 5. Embedding Generation (`backend/embedder.py`)
Embedding generation is the step where each text chunk is converted into a numeric vector so semantic similarity search can work in ChromaDB.

### How it fits in RAG flow
1. Documents are loaded and chunked in `backend/ingest.py`.
2. Chunk text is converted into vectors using an embedding model.
3. Vectors are stored in ChromaDB.
4. User query text is embedded into a query vector.
5. Top-`k` nearest chunk vectors are retrieved and passed to the LLM for answer generation.

### Key Functionality
*   **`get_embedder(use_google: bool = False)`**: Returns a LangChain-compatible embedding model.
*   **Local Mode (`use_google=False`)**:
    *   Uses `HuggingFaceEmbeddings` with `BAAI/bge-small-en-v1.5`.
    *   Runs offline after first download and avoids API costs.
    *   Uses normalized embeddings (`normalize_embeddings=True`) for better cosine similarity behavior.
*   **Google Mode (`use_google=True`)**:
    *   Uses `GoogleGenerativeAIEmbeddings` with `models/embedding-001`.
    *   Requires `GOOGLE_API_KEY`.
    *   Useful when preferring managed cloud embeddings over local model inference.

### Source Code:
```python
from config import settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings


def get_embedder(use_google: bool = False):
    """
    Returns the embedding model.

    use_google=False (default):
        Runs locally via HuggingFace — completely free, no API key.
        Downloads BAAI/bge-small-en-v1.5 on first run (~130MB).

    use_google=True:
        Uses Google's embedding API — free tier, needs GOOGLE_API_KEY.
        Slightly higher quality but requires internet on every call.
    """
    if use_google:
        # Google Generative AI Embeddings — free tier
        # Requires: pip install langchain-google-genai
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", google_api_key=settings.google_api_key
        )
    else:
        # Local HuggingFace model — fully free, works offline
        # Best balance of quality + speed for most projects
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},  # use "cuda" if you have a GPU
            encode_kwargs={"normalize_embeddings": True},  # improves cosine sim scores
        )


# ── Manual embedding example (to understand what's happening) ──
if __name__ == "__main__":
    embedder = get_embedder(use_google=False)  # local, free

    text = "What are the side effects of ibuprofen?"
    vector = embedder.embed_query(text)

    print(f"Text: {text}")
    print(f"Vector dims: {len(vector)}")  # → 384
    print(f"First 5 values: {vector[:5]}")  # → [0.23, -0.11, ...]
    print(f"Type: {type(vector)}")  # → list[float]
```

---

## 6. Vector Store Layer (`backend/vector_store.py`)
This module is responsible for connecting to ChromaDB and persisting chunk embeddings.

### Why this file exists
`ingest.py` prepares chunked `Document` objects, but those chunks are not searchable until they are converted into vectors and stored. `vector_store.py` handles that storage and later loading for retrieval.

### Key Functions
*   **`get_vector_store()`**
    *   Creates/loads a Chroma collection using:
        *   `settings.collection_name` (default: `ai_saas_docs`)
        *   `settings.chroma_persist_dir` (default: `./chroma_db`)
    *   Uses `get_embedder(use_google=False)` as the `embedding_function`.
    *   Important: the same embedding model must be used at ingest time and query time, otherwise similarity search quality drops.
*   **`ingest_to_store(chunks: list)`**
    *   Takes chunked LangChain `Document` objects.
    *   Calls `Chroma.from_documents(...)` which:
        *   Generates embeddings for chunk text
        *   Stores vectors + raw chunk text + metadata
        *   Persists data to disk and builds Chroma index structures
    *   Prints the number of stored chunks and returns the vector store instance.

### Source Code:
```python
from config import settings
from embedder import get_embedder
from langchain_community.vectorstores import Chroma


def get_vector_store():
    """
    Returns a Chroma vector store instance.
    Creates it if it doesn't exist, loads it if it does.
    """
    embedder = get_embedder(use_google=False)  # local HuggingFace, free

    vectorstore = Chroma(
        collection_name=settings.collection_name,
        embedding_function=embedder,
        persist_directory=settings.chroma_persist_dir,  # saves to disk
    )
    return vectorstore


def ingest_to_store(chunks: list) -> None:
    """
    Takes document chunks and stores them in the vector DB.
    Run this once (or when you add new documents).
    """
    embedder = get_embedder(use_google=False)  # must match get_vector_store()

    # This automatically:
    # 1. Generates embeddings for each chunk
    # 2. Stores embedding + raw text + metadata
    # 3. Builds the HNSW index
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedder,
        collection_name=settings.collection_name,
        persist_directory=settings.chroma_persist_dir,
    )

    print(f"✅ Stored {len(chunks)} chunks in ChromaDB")
    return vectorstore
```

### Typical Usage Flow
```python
from ingest import load_documents, chunk_documents
from vector_store import ingest_to_store, get_vector_store
from config import settings

docs = load_documents("./data")
chunks = chunk_documents(docs)
ingest_to_store(chunks)  # one-time or when data changes

vectorstore = get_vector_store()
results = vectorstore.similarity_search("your query here", k=settings.top_k)
```

---

## 7. Retrieval Smoke Test (`backend/query_test.py`)
This file is a retrieval-only test harness. It helps validate search quality before involving the LLM.

### Why this file matters
If retrieval returns irrelevant chunks, the final RAG answer will be wrong even with a good model. This script isolates retrieval so quality issues can be fixed early.

### Key Function
*   **`retrieve(query: str, top_k: int = settings.top_k)`**
    *   Loads the persisted vector store via `get_vector_store()`.
    *   Calls `similarity_search_with_score(...)` to return top-k matches.
    *   Returns a list of `(Document, float)` tuples.

### Source Code:
```python
from backend.vector_store import get_vector_store
from backend.config import settings


def retrieve(query: str, top_k: int = settings.top_k) -> list:
    """
    Core retrieval function.
    Returns top-k most relevant document chunks for a query.
    """
    vectorstore = get_vector_store()

    # similarity_search_with_score also returns the similarity score
    results = vectorstore.similarity_search_with_score(
        query=query,
        k=top_k
    )

    return results  # list of (Document, float) tuples
```

### What `__main__` does
*   Runs a sample query (`"What are the side effects of ibuprofen?"`).
*   Prints ranked results with:
    *   Similarity score
    *   Source metadata
    *   Preview of chunk text

---

## 8. RAG Engine (`backend/rag_engine.py`)
This is the end-to-end retrieval-augmented generation pipeline.

### Chain Design
`question` -> retriever -> context formatting -> prompt template -> Gemini model -> text output parser

### Key Components
*   **`SYSTEM_PROMPT`**
    *   Enforces grounded behavior:
        *   Answer only from provided context
        *   Say insufficient information when context is missing
        *   Avoid hallucinations
*   **`format_docs(docs)`**
    *   Joins retrieved chunks into one context string with separators.
*   **`build_rag_chain()`**
    *   Creates retriever from Chroma vector store.
    *   Initializes `ChatGoogleGenerativeAI` with settings (`model_name`, `temperature`, `google_api_key`).
    *   Builds LCEL chain with `RunnablePassthrough`, prompt, model, and `StrOutputParser`.
*   **`ask(question: str)`**
    *   Single public entry point for chat queries.
    *   Invokes chain and returns model text.

### Source Code:
```python
def build_rag_chain():
    """
    Creates the full RAG chain using LangChain's LCEL syntax.
    Chain: query -> retriever -> format -> prompt -> LLM -> parse
    """
    vectorstore = get_vector_store()

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.top_k}
    )

    llm = ChatGoogleGenerativeAI(
        model=settings.model_name,
        temperature=settings.temperature,
        google_api_key=settings.google_api_key,
        convert_system_message_to_human=True
    )

    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain
```

### Important Note
Current files use mixed import styles (`backend.module` vs `module`). Keep execution context consistent (or standardize imports) to avoid `ModuleNotFoundError`.

### Runtime Safety Updates Applied
The current `backend/rag_engine.py` now includes two practical safeguards:

*   **Dual import fallback**
    *   First tries package-style imports (`from backend...`) for `python -m backend.rag_engine`.
    *   Falls back to script-style imports (`from vector_store...`) for `python backend/rag_engine.py`.
    *   This reduces execution-context import errors during local development.
*   **Correct chain invocation input**
    *   `ask(question)` now calls `chain.invoke(question)` (raw string), not `chain.invoke({"question": question})`.
    *   This matches the LCEL mapping where `RunnablePassthrough()` expects the original question string input.
*   **LangChain v1-compatible imports**
    *   Uses `langchain_core.prompts`, `langchain_core.runnables`, and `langchain_core.output_parsers`.
    *   Prevents `ModuleNotFoundError: No module named 'langchain.prompts'` on modern LangChain versions.

---

## 9. FastAPI Layer (`backend/api.py`)
This module exposes the RAG engine as HTTP endpoints for frontend or external clients.

### Why this file exists
`rag_engine.py` provides Python functions (`ask`), but applications typically need network APIs. `api.py` wraps RAG behavior behind FastAPI routes so a UI (for example, Next.js) can call the chatbot over HTTP.

### Key Design Points
*   **FastAPI app initialization**
    *   App metadata: title `AI SaaS RAG API`, version `1.0.0`.
*   **CORS middleware**
    *   Allows requests from:
        *   `http://localhost:3000` (local frontend dev)
        *   `https://yourdomain.com` (production placeholder)
*   **Import fallback for runtime safety**
    *   First tries `from backend.rag_engine import ask`.
    *   Falls back to `from rag_engine import ask`.
    *   Fallback is restricted to backend package resolution failures so real nested import errors are not masked.
    *   Supports both module-style and script-style execution contexts.
*   **Typed API models**
    *   `AskRequest`: `question` + optional `chat_id` (default `"default"`).
    *   `AskResponse`: `answer`, `latency_ms`, `chat_id`.

### Endpoints
*   **`GET /`**
    *   Health check endpoint.
    *   Returns service status JSON.
*   **`POST /ask`**
    *   Validates non-empty question.
    *   Calls `ask(req.question)` from the RAG engine.
    *   Measures response latency and returns structured JSON.
    *   Converts runtime failures into `HTTP 500`.

### Source Code:
```python
@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest):
    """Main chatbot endpoint."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        start = time.time()
        answer = ask(req.question)
        latency = (time.time() - start) * 1000
        return AskResponse(
            answer=answer,
            latency_ms=round(latency, 2),
            chat_id=req.chat_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

### Run Command
```bash
uvicorn backend.api:app --reload --port 8000
```

### Example Request
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the side effects of ibuprofen?","chat_id":"demo"}'
```

### Example Response Shape
```json
{
  "answer": "string",
  "latency_ms": 123.45,
  "chat_id": "demo"
}
```

---

## 10. Current Workflow Status
The backend is now capable of:
- [x] **Loading multi-format data** (PDF, TXT, CSV, Excel, JSON)
- [x] **Chunking documents** with `RecursiveCharacterTextSplitter`
- [x] **Generating embeddings** via local HuggingFace or Google embeddings
- [x] **Persisting vectors to ChromaDB** using `backend/vector_store.py`
- [x] **Loading persisted vector store** for semantic retrieval
- [x] **Running retrieval-only validation** using `backend/query_test.py`
- [x] **Running full RAG answers** using `backend/rag_engine.py`
- [x] **Serving chat over HTTP** using `backend/api.py`

### Recommended Validation Commands
- `python backend/ingest.py`
- `python backend/query_test.py`
- `python backend/rag_engine.py`
- `python -m backend.rag_engine`
- `uvicorn backend.api:app --reload --port 8000`

**Next Steps**:
- Standardize imports across all backend modules (absolute or package-local consistently) so fallback imports are no longer needed.
- Add additional FastAPI endpoints for ingestion and retrieval diagnostics.
- Add automated tests for retrieval quality and chain invocation behavior.
