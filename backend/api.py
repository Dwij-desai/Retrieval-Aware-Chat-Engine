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


# ── STARTUP: pre-warm embedder + vector store ────────────────────
# Loads the HuggingFace model once at boot so the first real
# request is fast (~300ms) instead of slow (~10s).
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⏳ Pre-warming embedder and vector store...")
    t0 = time.time()
    get_vector_store()  # loads BAAI/bge-small-en-v1.5 into memory
    elapsed = round((time.time() - t0) * 1000)
    logger.info(f"✅ Vector store ready in {elapsed}ms — all requests will be fast.")
    yield
    # (shutdown logic goes here if needed)


app = FastAPI(title="AI SaaS RAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── MODELS ───────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str
    chat_id: str = "default"


class AskResponse(BaseModel):
    answer: str
    latency_ms: float
    chat_id: str


# ── ROUTES ───────────────────────────────────────────────────────
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
            detail=(
                "LLM quota/rate limit exceeded. "
                "Retry later or switch provider in .env. "
                f"Details: {exc}"
            ),
        ) from exc
    except ModelUnavailableError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Configured LLM models are unavailable. "
                "Update MODEL_NAME/GROQ_MODEL_NAME in .env. "
                f"Details: {exc}"
            ),
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
