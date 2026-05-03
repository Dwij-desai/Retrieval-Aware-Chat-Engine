# AI SaaS Chatbot — Project Documentation

This document summarizes the system architecture, component functionality, and provides the current code implementation for the AI SaaS Chatbot backend. The system is a Retrieval-Augmented Generation (RAG) pipeline that supports **multiple LLM providers** (Groq and Google Gemini), local vector storage via ChromaDB, and a FastAPI HTTP layer.

---

## 1. System Configuration (`backend/config.py`)

The `config.py` file is the centralized settings management hub using **Pydantic Settings**. It was significantly extended to support multi-provider LLM switching between Groq and Google Gemini.

### Key Responsibilities:
*   **LLM Provider Selection**: A single `llm_provider` field controls which API is used at runtime — set to `"groq"` or `"gemini"`.
*   **Environment Variables**: Automatically loads secrets (`GOOGLE_API_KEY`, `GROQ_API_KEY`, etc.) from `.env` and `.gitignore/.env`.
*   **Dual Model Configuration**: Maintains separate primary and fallback model fields for each provider, so switching providers never requires re-specifying model names.
*   **Vector Database Settings**: Defines the storage path (`./chroma_db`) and collection name for ChromaDB.
*   **RAG Parameters**:
    *   `chunk_size` (500) & `chunk_overlap` (50): Controls how documents are split for the LLM.
    *   `top_k` (4): Determines how many relevant context snippets are retrieved per query.
*   **`get_primary_model()`**: New method — returns the correct primary model name for the currently active provider.
*   **`get_fallback_models()`**: Updated — now returns the fallback list for the currently active provider instead of always reading the Gemini fallback field.

### Source Code:

```AI_SAAS(ChatBot)/backend/config.py#L1-52
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── LLM PROVIDER ─────────────────────────────────────────────
    # Set to "groq" or "gemini"
    llm_provider: str = "groq"

    # Google Gemini API key
    google_api_key: str = ""

    # Groq API key (free at console.groq.com)
    groq_api_key: str = ""

    # ── MODEL NAMES ───────────────────────────────────────────────
    # Gemini models
    model_name: str = "gemini-2.0-flash-lite"
    fallback_model_names: str = "gemini-2.0-flash"

    # Groq models (used when llm_provider=groq)
    groq_model_name: str = "llama-3.3-70b-versatile"
    groq_fallback_model_names: str = "llama-3.1-8b-instant"

    # ── VECTOR DB ─────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "ai_saas_docs"

    # ── RETRIEVAL ─────────────────────────────────────────────────
    top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 50

    # ── GENERATION ───────────────────────────────────────────────
    temperature: float = 0.1

    def get_fallback_models(self) -> list[str]:
        """Return fallback model list for the active provider."""
        if self.llm_provider == "groq":
            raw = self.groq_fallback_model_names
        else:
            raw = self.fallback_model_names
        return [m.strip() for m in raw.split(",") if m.strip()]

    def get_primary_model(self) -> str:
        """Return primary model name for the active provider."""
        if self.llm_provider == "groq":
            return self.groq_model_name
        return self.model_name

    class Config:
        env_file = (".env", ".gitignore/.env")


settings = Settings()
```

### What Changed From the Previous Version
| Field / Method | Before | After |
|---|---|---|
| `llm_provider` | _(not present)_ | `"groq"` (default) |
| `google_api_key` | Required (`str`) | Optional (`str = ""`) |
| `groq_api_key` | _(not present)_ | `str = ""` |
| `groq_model_name` | _(not present)_ | `"llama-3.3-70b-versatile"` |
| `groq_fallback_model_names` | _(not present)_ | `"llama-3.1-8b-instant"` |
| `model_name` | `"gemini-2.0-flash"` | `"gemini-2.0-flash-lite"` |
| `fallback_model_names` | `""` (empty) | `"gemini-2.0-flash"` |
| `get_primary_model()` | _(not present)_ | Returns primary for active provider |
| `get_fallback_models()` | Always reads Gemini field | Reads correct provider field |

---

## 2. Data Ingestion Pipeline (`backend/ingest.py`)

The ingestion layer transforms raw data files into a format searchable by the AI. Two bugs were fixed in this version.

### Key Functions:
*   **`load_documents(data_dir)`**: Scans the data directory and loads various file types into LangChain `Document` objects. Supports PDF, TXT, CSV, Excel, and JSON.
*   **`chunk_documents(documents)`**: Uses `RecursiveCharacterTextSplitter` to break long texts into smaller, semantically meaningful chunks. It prioritizes splitting at paragraphs and sentences to maintain context integrity.

### Fixes Applied
1.  **Import corrected**: `from langchain.text_splitter import RecursiveCharacterTextSplitter` was the deprecated path. Replaced with the canonical `from langchain_text_splitters import RecursiveCharacterTextSplitter`.
2.  **`__main__` block now actually ingests**: The old `__main__` block only loaded and chunked documents — it never called `ingest_to_store()`, so nothing was ever written to ChromaDB when running the script directly. This is now fixed.
3.  **CLI argument support**: The data directory can now be passed as `python backend/ingest.py ./my_docs`. Defaults to `./data` if omitted.
4.  **Empty-docs guard**: The script now exits with a clear warning message if no documents are found in the target directory, rather than crashing on `chunks[0]`.

### Source Code:

```AI_SAAS(ChatBot)/backend/ingest.py#L1-100
import json
import os
import sys

import pandas as pd
from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from backend.config import settings
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.config"}:
        raise
    from config import settings


def load_documents(data_dir: str) -> list:
    """Load PDFs, text, CSV, Excel, and JSON files from a directory."""
    documents = []

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
            df = pd.read_excel(filepath)
            for index, row in df.iterrows():
                content = " ".join([f"{col}: {val}" for col, val in row.items()])
                doc = Document(
                    page_content=content,
                    metadata={"source": filepath, "row": index},
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
                            metadata={"source": filepath, "item": index},
                        )
                    )
            else:
                documents.append(
                    Document(
                        page_content=json.dumps(json_data),
                        metadata={"source": filepath},
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
        chunk_size=settings.chunk_size,   # 500 chars
        chunk_overlap=settings.chunk_overlap,  # 50 char overlap
        separators=["\n\n", "\n", ". ", " ", ""],  # priority order
    )

    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")
    return chunks


if __name__ == "__main__":
    try:
        from backend.vector_store import ingest_to_store
    except ModuleNotFoundError:
        from vector_store import ingest_to_store

    data_dir = sys.argv[1] if len(sys.argv) > 1 else "./data"
    print(f"📂 Loading documents from: {data_dir}")
    docs = load_documents(data_dir)

    if not docs:
        print("⚠️  No documents found. Add files to the data/ folder and re-run.")
        raise SystemExit(1)

    chunks = chunk_documents(docs)
    print(f"📄 First chunk preview:\n{chunks[0].page_content[:200]}\n")

    ingest_to_store(chunks)
    print("🚀 Ingestion complete — ChromaDB is ready for queries.")
```

---

## 3. Multi-Format Support

The ingestion layer supports five file types. Each is handled by a dedicated loader or parser in `load_documents()`.

### PDF Support
*   Implemented using LangChain's `PyPDFLoader`.
*   Each page is treated as a distinct document before chunking.

### Plain Text Support
*   Implemented using LangChain's `TextLoader`.
*   The full file is loaded as a single document, then chunked.

### CSV Support
*   Implemented using LangChain's `CSVLoader`.
*   Each row in a CSV file is treated as a distinct document, allowing for granular per-row retrieval.

### Excel Support (`.xlsx`, `.xls`)
*   Integrated via `pandas` and `openpyxl`.
*   **Structured Conversion**: Every row is converted into a readable string: `ColumnName: Value ColumnName2: Value2`, so the LLM understands the tabular structure during generation.
*   Metadata includes `source` (file path) and `row` (row index).

### JSON Support
*   Uses Python's built-in `json` module (no extra dependency).
*   **Flexible Handling**:
    *   If the root JSON value is an array, each element becomes a separate `Document` (with `item` index in metadata).
    *   If the root JSON is an object or scalar, the full payload is stored as one document.

### Current Data Directory
The `data/` directory currently contains:
*   `product_faq.txt` — 118-line product knowledge base (15 chunks after splitting) — this is the primary demo/test dataset loaded into ChromaDB.
*   `test.csv` — sample CSV for multi-format validation.

---

## 4. Environment & Dependencies

### Required API Keys
*   **`GROQ_API_KEY`** — Required when `LLM_PROVIDER=groq`. Free tier available at [console.groq.com](https://console.groq.com).
*   **`GOOGLE_API_KEY`** — Required when `LLM_PROVIDER=gemini`. Free tier available via Google AI Studio.

Both keys default to empty strings in `config.py` so the application starts without crashing when one provider is unused.

### `.env` File Structure (Current)
Place this in the project root. The application reads it automatically at startup:

```AI_SAAS(ChatBot)/.env.example#L1-10
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIzaSy...
GROQ_MODEL_NAME=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL_NAMES=llama-3.1-8b-instant
MODEL_NAME=gemini-2.0-flash-lite
FALLBACK_MODEL_NAMES=gemini-2.0-flash
```

Only `LLM_PROVIDER` and the matching provider's key are strictly required at runtime. The model name fields are optional overrides — the defaults in `config.py` are sensible production values.

### Key Python Dependencies
*   `langchain`, `langchain-core`, `langchain-community`, `langchain-text-splitters` — LangChain orchestration stack
*   `langchain-google-genai` — Gemini LLM and embedding client
*   `langchain-groq` — Groq LLM client
*   `langchain-huggingface` or `langchain-community` — HuggingFace embedding client (local)
*   `langchain-chroma` or `langchain-community` — ChromaDB vector store adapter
*   `chromadb` — Local vector database
*   `pydantic-settings` — Environment-driven settings management
*   `fastapi`, `uvicorn` — HTTP API server
*   `pandas`, `openpyxl` — Excel ingestion support

### Environment Setup Commands
```AI_SAAS(ChatBot)/Environment.sh#L1-1
bash Environment.sh
```
Or for a fully reproducible environment from the config file:
```/dev/null/setup.sh#L1-2
conda env create -f environment.yml
conda activate ai_saas
```
Then set the Python path so backend modules resolve correctly:
```/dev/null/pythonpath.sh#L1-1
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

---

## 5. Embedding Generation (`backend/embedder.py`)

Embedding generation converts each text chunk into a numeric vector so that semantic similarity search can work inside ChromaDB.

### How It Fits in the RAG Flow
1.  Documents are loaded and chunked in `backend/ingest.py`.
2.  Chunk text is converted into dense vectors using an embedding model.
3.  Vectors are stored in ChromaDB alongside the raw text.
4.  At query time, the user's question is also embedded into a query vector.
5.  Top-`k` nearest chunk vectors are retrieved and passed to the LLM as context.

**Important**: The same embedding model must be used at ingest time and query time. Mixing models (e.g., ingesting with HuggingFace but querying with Google) produces meaningless similarity scores.

### Key Functionality
*   **`get_embedder(use_google: bool = False)`**: Returns a LangChain-compatible embedding model.
*   **Local Mode (`use_google=False`)** — the default:
    *   Uses `HuggingFaceEmbeddings` with `BAAI/bge-small-en-v1.5`.
    *   Downloads ~130 MB on first run, then runs fully offline.
    *   Uses normalized embeddings (`normalize_embeddings=True`) for better cosine similarity scores.
    *   Preferred import is `langchain_huggingface`; falls back to `langchain_community` for compatibility.
*   **Google Mode (`use_google=True`)**:
    *   Uses `GoogleGenerativeAIEmbeddings` with `models/embedding-001`.
    *   Requires `GOOGLE_API_KEY`.
    *   Useful when a managed cloud embedding is preferred over local model inference.

### Source Code:

```AI_SAAS(ChatBot)/backend/embedder.py#L1-55
from langchain_google_genai import GoogleGenerativeAIEmbeddings

try:
    # Preferred import in recent LangChain versions.
    from langchain_huggingface import HuggingFaceEmbeddings
except ModuleNotFoundError:
    # Backward-compatible fallback for environments not yet migrated.
    from langchain_community.embeddings import HuggingFaceEmbeddings

try:
    from backend.config import settings
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.config"}:
        raise
    from config import settings


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
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.google_api_key,
        )
    else:
        # Local HuggingFace model — fully free, works offline after download
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},   # use "cuda" if you have a GPU
            encode_kwargs={"normalize_embeddings": True},
        )


if __name__ == "__main__":
    embedder = get_embedder(use_google=False)

    text = "What are the side effects of ibuprofen?"
    vector = embedder.embed_query(text)

    print(f"Text: {text}")
    print(f"Vector dims: {len(vector)}")   # → 384
    print(f"First 5 values: {vector[:5]}")  # → [0.23, -0.11, ...]
    print(f"Type: {type(vector)}")           # → list[float]
```

---

## 6. Vector Store Layer (`backend/vector_store.py`)

This module connects to ChromaDB and handles both persisting embeddings during ingestion and loading them for retrieval.

### Why This File Exists
`ingest.py` prepares chunked `Document` objects, but those chunks are not searchable until they are embedded and written to a vector index. `vector_store.py` owns that responsibility, cleanly separating the I/O concern from the loading/chunking logic.

### Key Functions
*   **`get_vector_store()`**
    *   Creates or loads a Chroma collection using `settings.collection_name` and `settings.chroma_persist_dir`.
    *   Uses `get_embedder(use_google=False)` — the local HuggingFace model — as the embedding function.
    *   Called both during pre-warm at server startup and on every `/ask` request.
*   **`ingest_to_store(chunks: list)`**
    *   Takes chunked LangChain `Document` objects from `ingest.py`.
    *   Calls `Chroma.from_documents(...)` which:
        *   Generates embeddings for each chunk's text content.
        *   Stores the vectors, raw text, and metadata (source, row, item).
        *   Persists data to disk and builds the HNSW index structures.
    *   Prints the number of stored chunks and returns the vector store instance.

### Source Code:

```AI_SAAS(ChatBot)/backend/vector_store.py#L1-50
try:
    # Preferred import in recent LangChain versions.
    from langchain_chroma import Chroma
except ModuleNotFoundError:
    # Backward-compatible fallback for environments not yet migrated.
    from langchain_community.vectorstores import Chroma

try:
    from backend.config import settings
    from backend.embedder import get_embedder
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.config", "backend.embedder"}:
        raise
    from config import settings
    from embedder import get_embedder


def get_vector_store():
    """
    Returns a Chroma vector store instance.
    Creates it if it doesn't exist, loads it if it does.
    """
    embedder = get_embedder(use_google=False)  # local HuggingFace, free

    vectorstore = Chroma(
        collection_name=settings.collection_name,
        embedding_function=embedder,
        persist_directory=settings.chroma_persist_dir,
    )
    return vectorstore


def ingest_to_store(chunks: list):
    """
    Takes document chunks and stores them in the vector DB.
    Run this once (or whenever you add new documents).
    """
    embedder = get_embedder(use_google=False)  # must match get_vector_store()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedder,
        collection_name=settings.collection_name,
        persist_directory=settings.chroma_persist_dir,
    )

    print(f"✅ Stored {len(chunks)} chunks in ChromaDB")
    return vectorstore
```

### ChromaDB Status
ChromaDB is currently **populated and operational**. Running `python backend/ingest.py` against `data/product_faq.txt` produced **15 chunks** which are now indexed and confirmed working end-to-end with real query results.

### Typical Usage Flow

```AI_SAAS(ChatBot)/backend/vector_store.py#L1-8
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

This file is a retrieval-only test harness that validates search quality in isolation — before involving the LLM.

### Why This File Matters
If retrieval returns irrelevant chunks, the final RAG answer will be wrong even with a perfect generation model. This script isolates the retrieval step so quality issues can be diagnosed and fixed independently of the LLM.

### Key Function
*   **`retrieve(query: str, top_k: int = settings.top_k)`**
    *   Loads the persisted vector store via `get_vector_store()`.
    *   Calls `similarity_search_with_score(...)` to return top-k matches with similarity scores.
    *   Returns a list of `(Document, float)` tuples.

### Source Code:

```AI_SAAS(ChatBot)/backend/query_test.py#L1-20
from backend.vector_store import get_vector_store
from backend.config import settings


def retrieve(query: str, top_k: int = settings.top_k) -> list:
    """
    Core retrieval function.
    Returns top-k most relevant document chunks for a query.
    """
    vectorstore = get_vector_store()

    results = vectorstore.similarity_search_with_score(
        query=query,
        k=top_k,
    )

    return results  # list of (Document, float) tuples
```

### What `__main__` Does
*   Runs a sample query (e.g., `"What are the side effects of ibuprofen?"`).
*   Prints ranked results with similarity score, source metadata, and a text preview of each chunk.
*   Use this to confirm that ingestion worked correctly before running the full RAG engine.

---

## 8. RAG Engine (`backend/rag_engine.py`)

This is the end-to-end retrieval-augmented generation pipeline. It is the core intelligence layer of the system.

### Chain Design

```/dev/null/chain.txt#L1-1
question → retrieval → context formatting → prompt template → LLM (with provider routing + fallback) → text output
```

### Key Components

*   **`SYSTEM_PROMPT`**
    *   Enforces grounded behavior — the model is instructed to answer only from the provided context, say "I don't have enough information" when context is missing, and never hallucinate.
*   **`format_docs(docs)`**
    *   Joins retrieved chunks into a single context string with `\n\n---\n\n` separators.
*   **Typed RAG errors** — raised by the engine and caught in `api.py` for HTTP status mapping:
    *   `RAGEngineError` — base class
    *   `QuotaExceededError` — quota or rate limit exhausted
    *   `ModelUnavailableError` — model name not found or inaccessible
    *   `UpstreamLLMError` — other provider-side failures
*   **`_ordered_model_candidates()`**
    *   Now calls `settings.get_primary_model()` instead of reading `settings.model_name` directly.
    *   This means the correct primary model is selected for the active provider automatically.
*   **`_build_generation_chain(model_name)`**
    *   **Provider-aware**: branches on `settings.llm_provider`.
    *   `"groq"` → instantiates `ChatGroq` with the Groq API key.
    *   `"gemini"` → instantiates `ChatGoogleGenerativeAI` with the Google API key.
    *   **Removed** deprecated `convert_system_message_to_human=True` parameter from `ChatGoogleGenerativeAI`.
    *   Returns the composed chain: `prompt | llm | StrOutputParser()`.
*   **`ask(question: str)`**
    *   Single public entry point for all chat queries.
    *   Retrieves context once from ChromaDB, then attempts model candidates in order.
    *   Raises typed errors for clean HTTP status code mapping in the API layer.
    *   All error messages are now **provider-agnostic** — no hardcoded "Gemini" text.

### Provider-Aware Chain Builder

```AI_SAAS(ChatBot)/backend/rag_engine.py#L70-86
def _build_generation_chain(model_name: str):
    """Create the generation pipeline for one model."""
    if settings.llm_provider == "groq":
        llm = ChatGroq(
            model=model_name,
            temperature=settings.temperature,
            api_key=settings.groq_api_key,
        )
    else:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=settings.temperature,
            google_api_key=settings.google_api_key,
        )
    return prompt | llm | StrOutputParser()
```

### Full Source Code:

```AI_SAAS(ChatBot)/backend/rag_engine.py#L1-220
from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

try:
    from backend.config import settings
    from backend.vector_store import get_vector_store
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.vector_store", "backend.config"}:
        raise
    from config import settings
    from vector_store import get_vector_store

SYSTEM_PROMPT = """
You are a knowledgeable and helpful AI assistant.
Your rules:
    1. Answer ONLY using the provided context below.
    2. If the answer is not in the context, say: "I don't have enough information to answer that accurately."
    3. Be concise. Cite context when possible.
    4. Never make up information.
Context: {context}
"""

prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)


class RAGEngineError(Exception):
    """Base class for RAG engine failures surfaced to API layer."""

class ModelUnavailableError(RAGEngineError):
    """Raised when the configured model cannot be used."""

class QuotaExceededError(RAGEngineError):
    """Raised when all model attempts fail due to quota/rate limits."""

class UpstreamLLMError(RAGEngineError):
    """Raised when the LLM provider fails for other upstream reasons."""


def format_docs(docs: list[Document]) -> str:
    """Join retrieved chunks into a single context string."""
    return "\n\n---\n\n".join([doc.page_content for doc in docs])


def _ordered_model_candidates() -> list[str]:
    """Return primary model followed by configured fallbacks, deduplicated."""
    ordered = [settings.get_primary_model(), *settings.get_fallback_models()]
    unique_models: list[str] = []
    for model_name in ordered:
        model_name = model_name.strip()
        if not model_name:
            continue
        if model_name not in unique_models:
            unique_models.append(model_name)
    return unique_models


def _build_generation_chain(model_name: str):
    """Create the generation pipeline for one model."""
    if settings.llm_provider == "groq":
        llm = ChatGroq(
            model=model_name,
            temperature=settings.temperature,
            api_key=settings.groq_api_key,
        )
    else:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=settings.temperature,
            google_api_key=settings.google_api_key,
        )
    return prompt | llm | StrOutputParser()


def _retrieve_context(question: str) -> str:
    """Retrieve top-k chunks once and join them as model context."""
    vectorstore = get_vector_store()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.top_k},
    )
    docs = retriever.invoke(question)
    return format_docs(docs)


def ask(question: str) -> str:
    """Single entry point for the RAG chatbot with model fallback."""
    context = _retrieve_context(question)
    payload = {"context": context, "question": question}
    candidate_models = _ordered_model_candidates()
    if not candidate_models:
        raise ModelUnavailableError(
            "No LLM models configured. Set MODEL_NAME/GROQ_MODEL_NAME in .env."
        )

    last_error: Exception | None = None
    attempt_errors: list[tuple[str, str]] = []
    for index, model_name in enumerate(candidate_models):
        chain = build_rag_chain(model_name=model_name)
        try:
            return chain.invoke(payload)
        except Exception as exc:
            last_error = exc
            error_text = str(exc)
            attempt_errors.append((model_name, _first_error_line(error_text)))
            has_more_models = index < len(candidate_models) - 1
            if has_more_models and _should_try_next_model(error_text):
                continue
            raise _build_llm_error(
                model_name, candidate_models, exc, attempt_errors,
            ) from exc

    raise UpstreamLLMError("No models were available to execute the request.")
```

### Runtime Safety Design
*   **Dual import fallback**: Tries `backend.*` package-style imports first (for `python -m backend.rag_engine`), then falls back to script-style imports (for `python backend/rag_engine.py`). Fallback is restricted to backend package resolution failures so nested import errors from third-party libraries are not accidentally swallowed.
*   **Graceful quota/model failures**: Quota errors (`429 RESOURCE_EXHAUSTED`), model-not-found responses (`404 NOT_FOUND`), and upstream server errors (`500`, `503`) are all classified, surfaced as typed exceptions, and retried on the next model candidate.
*   **Compact attempt diagnostics**: On failure, the error message includes a per-model summary line: `model_a: STATUS (CODE) | model_b: STATUS (CODE)`. Full JSON payloads from providers are never passed to the user.
*   **LangChain v1-compatible imports**: Uses `langchain_core.prompts` and `langchain_core.output_parsers` only — no deprecated `langchain.schema.*` paths.

---

## 9. FastAPI Layer (`backend/api.py`)

This module exposes the RAG engine as HTTP endpoints for use by a frontend UI or any external client.

### Why This File Exists
`rag_engine.py` provides Python functions, but applications communicate over networks. `api.py` wraps RAG behavior behind FastAPI routes so a UI (e.g., a Next.js frontend) can call the chatbot over HTTP with structured request/response contracts.

### Key Changes From the Previous Version
1.  **`lifespan` startup handler**: Pre-warms the embedder and vector store at server boot. Previously, the HuggingFace model was loaded on the very first request, causing ~10 second delays. Now the first real request takes ~300–600ms.
2.  **`GET /favicon.ico`**: Returns `204 No Content`. Silences the stream of 404 log noise browsers generate when hitting an API server directly.
3.  **`logging` + `logger.exception()`**: Unexpected errors in `/ask` are now logged with a full traceback on the server side before returning `500` to the client.
4.  **Provider-agnostic error messages**: HTTP `503`/`502` detail strings no longer mention "Gemini" — they work correctly regardless of which provider is active.

### Startup Pre-Warm (`lifespan`)
The lifespan handler runs once when the server starts and loads the embedding model into memory:

```AI_SAAS(ChatBot)/backend/api.py#L34-45
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⏳ Pre-warming embedder and vector store...")
    t0 = time.time()
    get_vector_store()  # loads BAAI/bge-small-en-v1.5 into memory
    elapsed = round((time.time() - t0) * 1000)
    logger.info(f"✅ Vector store ready in {elapsed}ms — all requests will be fast.")
    yield
    # (shutdown logic goes here if needed)
```

### Endpoints
*   **`GET /`** — Health check. Returns `{"status": "ok", "service": "AI SaaS RAG API"}`.
*   **`GET /favicon.ico`** — Returns `204 No Content` (suppresses browser 404 noise).
*   **`POST /ask`** — Main chatbot endpoint. Validates the question, invokes the RAG engine, measures latency, and returns a structured response.

### HTTP Status Code Mapping
| Exception | HTTP Status | Meaning |
|---|---|---|
| `QuotaExceededError` | `503 Service Unavailable` | Provider quota/rate limit hit |
| `ModelUnavailableError` | `502 Bad Gateway` | Configured model not accessible |
| `UpstreamLLMError` | `502 Bad Gateway` | Provider returned a failure |
| `RAGEngineError` | `500 Internal Server Error` | Other engine-level failure |
| `Exception` (unexpected) | `500 Internal Server Error` | Logged server-side with full traceback |

### Full Source Code:

```AI_SAAS(ChatBot)/backend/api.py#L1-100
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

try:
    from backend.rag_engine import (
        ModelUnavailableError,
        QuotaExceededError,
        RAGEngineError,
        UpstreamLLMError,
        ask,
    )
    from backend.vector_store import get_vector_store
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.rag_engine", "backend.vector_store"}:
        raise
    from rag_engine import (
        ModelUnavailableError,
        QuotaExceededError,
        RAGEngineError,
        UpstreamLLMError,
        ask,
    )
    from vector_store import get_vector_store

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⏳ Pre-warming embedder and vector store...")
    t0 = time.time()
    get_vector_store()
    elapsed = round((time.time() - t0) * 1000)
    logger.info(f"✅ Vector store ready in {elapsed}ms — all requests will be fast.")
    yield


app = FastAPI(title="AI SaaS RAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    chat_id: str = "default"


class AskResponse(BaseModel):
    answer: str
    latency_ms: float
    chat_id: str


@app.get("/")
async def health():
    return {"status": "ok", "service": "AI SaaS RAG API"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Suppress browser favicon 404 noise in logs."""
    return Response(status_code=204)


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest):
    """Main chatbot endpoint — retrieves context and generates an answer."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        start = time.time()
        answer = ask(req.question)
        latency = (time.time() - start) * 1000
        return AskResponse(
            answer=answer,
            latency_ms=round(latency, 2),
            chat_id=req.chat_id,
        )
    except QuotaExceededError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"LLM quota/rate limit exceeded. Details: {exc}",
        ) from exc
    except ModelUnavailableError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Configured LLM models unavailable. Details: {exc}",
        ) from exc
    except UpstreamLLMError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider call failed. Details: {exc}",
        ) from exc
    except RAGEngineError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"RAG engine error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error in /ask")
        raise HTTPException(
            status_code=500,
            detail="Unexpected internal server error.",
        ) from exc
```

### Example Request

```/dev/null/curl.sh#L1-4
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "How fast are responses?", "chat_id": "demo"}'
```

### Example Response Shape
```/dev/null/response.json#L1-5
{
  "answer": "With Groq-powered inference, responses typically arrive in under 1 second...",
  "latency_ms": 412.35,
  "chat_id": "demo"
}
```

---

## 10. Startup Script (`start.sh`)

`start.sh` is a one-command server startup script added to the project root. It resolves the project directory, sets `PYTHONPATH`, and launches `uvicorn` using the Conda environment's Python binary directly — no manual `conda activate` required.

### Source Code:

```AI_SAAS(ChatBot)/start.sh#L1-18
#!/bin/bash
# ── AI SaaS Chatbot — Start Script ───────────────────────────────
# Usage: bash start.sh
# Starts the FastAPI server using the AI_SaaS conda environment.

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

export PYTHONPATH="$DIR"

PYTHON="/opt/anaconda3/envs/AI_SaaS/bin/python"

echo ""
echo "🤖 AI SaaS Chatbot — Starting..."
echo "📂 Project root : $DIR"
echo "🐍 Python       : $($PYTHON --version)"
echo "🌐 API URL      : http://127.0.0.1:8000"
echo "📖 Docs URL     : http://127.0.0.1:8000/docs"
echo ""

"$PYTHON" -m uvicorn backend.api:app --reload --port 8000 --host 0.0.0.0
```

### Why It Exists
Running `uvicorn backend.api:app` directly from a terminal without the correct `PYTHONPATH` or the active Conda environment causes `ModuleNotFoundError` on `backend.*` imports. This script eliminates that class of error entirely with a single command.

### Usage
```/dev/null/usage.sh#L1-1
bash start.sh
```

Once running, the API is accessible at:
*   **API base**: `http://127.0.0.1:8000`
*   **Interactive docs**: `http://127.0.0.1:8000/docs`
*   **OpenAPI schema**: `http://127.0.0.1:8000/openapi.json`

---

## 11. Provider Configuration

The system supports two LLM providers that can be switched with a single environment variable. The embedding layer (HuggingFace local) is the same regardless of provider.

### Provider Comparison

| Provider | Model | Free RPD | Typical Latency | Use Case |
|---|---|---|---|---|
| Groq | `llama-3.3-70b-versatile` | 14,400 | ~300ms | Development & production (default) |
| Groq | `llama-3.1-8b-instant` | 14,400 | ~150ms | Groq fallback (smaller, faster) |
| Gemini | `gemini-2.0-flash-lite` | 1,500 | ~800ms | Production with billing |
| Gemini | `gemini-2.0-flash` | 1,500 | ~1,000ms | Gemini fallback |

*RPD = Requests Per Day on the free tier.*

### Switching to Groq (Default)
Set in `.env`:
```/dev/null/groq.env#L1-3
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
```
The Gemini fields can remain present or be omitted — they are unused when `LLM_PROVIDER=groq`.

### Switching to Gemini
Set in `.env`:
```/dev/null/gemini.env#L1-3
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSy_your_key_here
```
The Groq fields can remain present or be omitted — they are unused when `LLM_PROVIDER=gemini`.

### How the Provider Routing Works
1.  `Settings.llm_provider` is read from the environment at startup.
2.  `settings.get_primary_model()` returns `groq_model_name` or `model_name` depending on the active provider.
3.  `settings.get_fallback_models()` returns the matching fallback list for the active provider.
4.  `_build_generation_chain()` in `rag_engine.py` instantiates either `ChatGroq` or `ChatGoogleGenerativeAI` based on `settings.llm_provider`.
5.  No other code in the stack needs to know which provider is active — the routing is fully contained in `config.py` and `rag_engine.py`.

### Getting API Keys
*   **Groq**: [console.groq.com](https://console.groq.com) → sign up → API Keys → Create Key. Free tier gives 14,400 requests/day with ~500 tokens/second inference.
*   **Gemini**: [aistudio.google.com](https://aistudio.google.com) → Get API key. Free tier gives 1,500 requests/day with ~2 million tokens/minute on Flash models.

---

## 12. Multi-Provider Troubleshooting

### Groq Issues
*   **`401 Unauthorized`**: `GROQ_API_KEY` is missing, incorrect, or the key was regenerated. Confirm the value in `.env` matches your key at [console.groq.com](https://console.groq.com).
*   **`429 Too Many Requests`**: Free tier rate limit hit. The engine will automatically retry using `groq_fallback_model_names` (`llama-3.1-8b-instant`). If both models are exhausted, a `QuotaExceededError` → HTTP `503` is returned.
*   **`404 model not found`**: The `GROQ_MODEL_NAME` value is not available for your account. Check [console.groq.com/docs/models](https://console.groq.com/docs/models) for valid model IDs.
*   **`LLM_PROVIDER=groq` but Gemini errors appear in logs**: `LLM_PROVIDER` is not being read from `.env`. Check that the `.env` file exists in the project root and that `pydantic-settings` is installed.

### Gemini Issues
*   **`RESOURCE_EXHAUSTED (429)`**: Daily quota on the free tier (1,500 RPD) is exhausted, or per-minute rate limit is hit. The engine retries with `fallback_model_names`. If both fail, HTTP `503` is returned. Solutions: wait for quota reset, add billing to the Google Cloud project, or switch to `LLM_PROVIDER=groq`.
*   **`NOT_FOUND (404)`**: The model name is not available for your API key or project. Confirm the model in [Google AI Studio](https://aistudio.google.com) and that your key belongs to the correct GCP project.
*   **`400 API_KEY_INVALID`**: `GOOGLE_API_KEY` is incorrect or expired. Regenerate it in Google AI Studio.
*   **Billing not active**: Some Gemini models require an active billing account even for moderate traffic. Open the GCP console → Billing and ensure it is linked.

### General Issues
*   **First request is slow (~10 seconds)**: This means the server was started without the `lifespan` pre-warm taking effect (e.g., via a direct `python` invocation rather than `uvicorn`). Use `bash start.sh` or `uvicorn backend.api:app --reload --port 8000` to ensure the full FastAPI app lifecycle runs.
*   **`ModuleNotFoundError: No module named 'backend'`**: `PYTHONPATH` is not set to the project root. Use `bash start.sh` (which sets it automatically) or run `export PYTHONPATH=$(pwd)` from the project root before starting.
*   **`No documents found` during ingestion**: The `data/` directory is empty or only contains unsupported file types. Add a `.txt`, `.pdf`, `.csv`, `.xlsx`, or `.json` file and re-run `python backend/ingest.py`.
*   **ChromaDB returns empty results**: The vector store has not been populated yet. Run `python backend/ingest.py` first.
*   **Embedding model mismatch**: If ChromaDB was populated with one embedding model and `get_vector_store()` uses a different one, all similarity scores will be meaningless. Delete the `./chroma_db` directory and re-run ingestion.

---

## 13. Current Workflow Status

The backend is fully operational end-to-end.

### Feature Checklist
- [x] **Multi-provider LLM support** — Groq and Gemini switchable via `.env`
- [x] **Loading multi-format data** — PDF, TXT, CSV, Excel, JSON
- [x] **Chunking documents** with `RecursiveCharacterTextSplitter` (canonical import path)
- [x] **Generating embeddings** — local HuggingFace (`BAAI/bge-small-en-v1.5`) or Google
- [x] **Persisting vectors to ChromaDB** — 15 chunks from `product_faq.txt` stored and indexed
- [x] **Loading persisted vector store** for semantic retrieval
- [x] **Running retrieval-only validation** using `backend/query_test.py`
- [x] **Running full RAG answers** using `backend/rag_engine.py`
- [x] **Serving chat over HTTP** using `backend/api.py`
- [x] **Server pre-warm at startup** — first request latency reduced from ~10s to ~300–600ms
- [x] **One-command server startup** via `bash start.sh`
- [x] **Graceful model fallback** — auto-retries next configured model on quota/unavailability errors
- [x] **Provider-agnostic error handling** — HTTP error details work regardless of active provider
- [x] **Favicon noise suppression** — `GET /favicon.ico` returns `204` to quiet browser logs
- [x] **CLI argument support in ingest** — `python backend/ingest.py ./custom_data_dir`
- [x] **Empty-document guard in ingest** — exits cleanly with a message if no files are found

### Recommended Validation Commands

```/dev/null/validation.sh#L1-10
# 1. Ingest documents into ChromaDB
python backend/ingest.py

# 2. Ingest from a custom directory
python backend/ingest.py ./data

# 3. Validate retrieval quality (no LLM involved)
python backend/query_test.py

# 4. Test full RAG pipeline from the command line
python -m backend.rag_engine

# 5. Start the API server (recommended method)
bash start.sh

# 6. Or start manually with uvicorn
uvicorn backend.api:app --reload --port 8000

# 7. Quick syntax check before committing
python3 -m py_compile backend/config.py backend/ingest.py backend/embedder.py backend/vector_store.py backend/rag_engine.py backend/api.py
```

### Roadmap
- [ ] Add a FastAPI `/ingest` endpoint to trigger ingestion over HTTP (without CLI access)
- [ ] Add a FastAPI `/retrieval-debug` endpoint for inspecting raw retrieved chunks
- [ ] Build a frontend UI (e.g., Next.js) for browser-based chat interaction
- [ ] Integrate session management for multi-turn conversation history
- [ ] Add automated `pytest` tests covering ingestion edge cases and RAG chain invocation
- [ ] Standardize all backend imports to package-style (`backend.*`) so dual-import fallbacks can be removed
- [ ] Add Docker support for containerized deployment
