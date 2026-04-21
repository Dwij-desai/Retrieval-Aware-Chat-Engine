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

    # LLM default set to a currently available Gemini family model.
    # Override with MODEL_NAME in env if needed.
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.1

    class Config:
        env_file = (".env", ".gitignore/.env")


settings = Settings()
