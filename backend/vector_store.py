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
