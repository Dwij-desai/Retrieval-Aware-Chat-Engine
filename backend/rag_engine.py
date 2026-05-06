from __future__ import annotations

import re
import time

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

try:
    # Package-style imports (e.g., `python -m backend.rag_engine`)
    from backend.config import settings
    from backend.vector_store import get_vector_store
    from backend.observability import enable_langsmith_tracing
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.vector_store", "backend.config", "backend.observability"}:
        raise
    # Script-style imports (e.g., `python backend/rag_engine.py`)
    from config import settings
    from vector_store import get_vector_store
    from observability import enable_langsmith_tracing

# Enable LangSmith tracing if API key is available
enable_langsmith_tracing()

# ── 1. THE PROMPT TEMPLATE ──────────────────────────────────────
# This is where most developers get lazy. A good prompt makes
# the difference between a hallucinating bot and an accurate one.

SYSTEM_PROMPT = """
You are a knowledgeable and helpful AI assistant.
Your rules:
    1. Answer ONLY using the provided context below.
    2. If the answer is not in the context, say: "I don't have enough information to answer that accurately."
    3. Use conversation history to resolve follow-ups (e.g., "it", "they").
    4. Be concise. Do not repeat earlier answers unless asked.
    5. Never make up information.
Context: {context}
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)


# ── 2. DOMAIN ERRORS ─────────────────────────────────────────────
class RAGEngineError(Exception):
    """Base class for RAG engine failures surfaced to API layer."""


class ModelUnavailableError(RAGEngineError):
    """Raised when the configured Gemini model cannot be used."""


class QuotaExceededError(RAGEngineError):
    """Raised when all model attempts fail due to quota/rate limits."""


class UpstreamLLMError(RAGEngineError):
    """Raised when the Gemini API fails for other upstream reasons."""


# ── 3. FORMAT RETRIEVED DOCS ────────────────────────────────────
def format_docs(docs: list[Document]) -> str:
    """Join retrieved chunks into a single context string."""
    return "\n\n---\n\n".join([doc.page_content for doc in docs])


# ── 4. RAG BUILDING BLOCKS ──────────────────────────────────────
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


def _history_to_messages(chat_history: list[tuple[str, str]] | None) -> list:
    """Convert stored chat history into LangChain message objects."""
    if not chat_history:
        return []
    messages = []
    for role, content in chat_history:
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def _build_retrieval_query(
    question: str, chat_history: list[tuple[str, str]] | None
) -> str:
    """Blend recent chat history into the retrieval query for follow-ups."""
    if not chat_history:
        return question
    recent = chat_history[-4:]
    history_lines = [f"{role}: {content}" for role, content in recent]
    history_block = "\n".join(history_lines)
    return f"Conversation history:\n{history_block}\nFollow-up question: {question}"


def _retrieve_context(question: str, chat_history: list[tuple[str, str]] | None) -> str:
    """Retrieve top-k chunks once and join them as model context."""
    vectorstore = get_vector_store()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.top_k},
    )
    retrieval_query = _build_retrieval_query(question, chat_history)
    docs = retriever.invoke(retrieval_query)
    return format_docs(docs)


def _is_quota_error(error_text: str) -> bool:
    lowered = error_text.lower()
    markers = [
        "resource_exhausted",
        "quota",
        "rate limit",
        "too many requests",
        "429",
    ]
    return any(marker in lowered for marker in markers)


def _is_model_unavailable_error(error_text: str) -> bool:
    lowered = error_text.lower()
    return (
        "not_found" in lowered and "model" in lowered
    ) or "model is not found" in lowered


def _is_upstream_retryable_error(error_text: str) -> bool:
    lowered = error_text.lower()
    markers = [
        "service unavailable",
        "unavailable",
        "deadline exceeded",
        "timed out",
        "internal",
        "503",
        "500",
    ]
    return any(marker in lowered for marker in markers)


def _first_error_line(error_text: str) -> str:
    """Keep user-facing error payload compact for API responses."""
    compact = " ".join(error_text.split())
    status_match = re.search(r"\(([^)]+)\):\s*(\d{3})", compact)
    if status_match:
        status = status_match.group(1)
        code = status_match.group(2)
        return f"{status} ({code})"
    if len(compact) <= 240:
        return compact
    return f"{compact[:237]}..."


def _format_attempt_diagnostics(attempt_errors: list[tuple[str, str]]) -> str:
    """Format per-model failures into one compact string."""
    if not attempt_errors:
        return "No attempt diagnostics captured."
    return " | ".join([f"{model}: {error}" for model, error in attempt_errors])


def _build_llm_error(
    model_name: str,
    all_models: list[str],
    raw_error: Exception,
    attempt_errors: list[tuple[str, str]] | None = None,
) -> RAGEngineError:
    error_text = str(raw_error)
    compact_error = _first_error_line(error_text)
    model_list = ", ".join(all_models)
    diagnostics = _format_attempt_diagnostics(attempt_errors or [])

    if _is_quota_error(error_text):
        return QuotaExceededError(
            "LLM quota/rate limit exceeded for attempted models "
            f"[{model_list}]. Last failure on '{model_name}': {compact_error}. "
            f"Attempt diagnostics: {diagnostics}"
        )

    if _is_model_unavailable_error(error_text):
        return ModelUnavailableError(
            "No configured LLM model could be used. Attempted models: "
            f"[{model_list}]. Last failure on '{model_name}': {compact_error}. "
            f"Attempt diagnostics: {diagnostics}"
        )

    return UpstreamLLMError(
        "LLM provider failed after trying models "
        f"[{model_list}]. Last failure on '{model_name}': {compact_error}. "
        f"Attempt diagnostics: {diagnostics}"
    )


def _should_try_next_model(error_text: str) -> bool:
    return (
        _is_quota_error(error_text)
        or _is_model_unavailable_error(error_text)
        or _is_upstream_retryable_error(error_text)
    )


# ── 5. BUILD THE RAG CHAIN ──────────────────────────────────────
def build_rag_chain(model_name: str):
    """Creates the generation chain for one model."""
    return _build_generation_chain(model_name=model_name)


# ── 6. MAIN ASK FUNCTION ────────────────────────────────────────
def ask(question: str, chat_history: list[tuple[str, str]] | None = None) -> str:
    """Single entry point for the RAG chatbot with model fallback."""
    start_time = time.time()
    context = _retrieve_context(question, chat_history)
    history_messages = _history_to_messages(chat_history)
    payload = {"context": context, "question": question, "history": history_messages}
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
            result = chain.invoke(payload)
            latency_ms = (time.time() - start_time) * 1000
            return result
        except Exception as exc:
            last_error = exc
            error_text = str(exc)
            attempt_errors.append((model_name, _first_error_line(error_text)))
            has_more_models = index < len(candidate_models) - 1
            if has_more_models and _should_try_next_model(error_text):
                continue
            raise _build_llm_error(
                model_name,
                candidate_models,
                exc,
                attempt_errors,
            ) from exc

    if last_error is not None:
        raise _build_llm_error(
            candidate_models[-1],
            candidate_models,
            last_error,
            attempt_errors,
        ) from last_error

    raise UpstreamLLMError("No models were available to execute the request.")


if __name__ == "__main__":
    try:
        answer = ask("What are the side effects of ibuprofen?")
        print(f"\nAnswer:\n{answer}")
    except RAGEngineError as exc:
        print(f"\nRAG engine error: {exc}\nCheck your .env provider settings.")
        raise SystemExit(1)
