from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

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
        # Google Generative AI Embeddings — free tier
        # Requires: pip install langchain-google-genai
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.google_api_key,
        )
    else:
        # Local HuggingFace model — fully free, works offline
        # Best balance of quality + speed for most projects
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},  # use "cuda" if you have a GPU
            encode_kwargs={
                "normalize_embeddings": True
            },  # improves cosine sim scores
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
