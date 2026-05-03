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
