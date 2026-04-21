import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    # Package-style import (e.g., `uvicorn backend.api:app --reload`)
    from backend.rag_engine import ask
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.rag_engine"}:
        raise
    # Script-style import fallback
    from rag_engine import ask


app = FastAPI(title="AI SaaS RAG API", version="1.0.0")

# Allow local frontend + placeholder production domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    chat_id: str = "default"  # placeholder for future multi-session support


class AskResponse(BaseModel):
    answer: str
    latency_ms: float
    chat_id: str


@app.get("/")
async def health():
    return {"status": "ok", "service": "AI SaaS RAG API"}


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
        error_text = str(exc)
        if "NOT_FOUND" in error_text and "model" in error_text.lower():
            raise HTTPException(
                status_code=502,
                detail=(
                    "Configured Gemini model is unavailable. "
                    "Update MODEL_NAME (or backend/config.py model_name) "
                    "to a supported model such as gemini-2.0-flash."
                ),
            ) from exc
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# Run with:
# uvicorn backend.api:app --reload --port 8000