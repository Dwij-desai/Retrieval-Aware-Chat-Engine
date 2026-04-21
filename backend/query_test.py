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


if __name__ == "__main__":
    query = "What are the side effects of ibuprofen?"
    results = retrieve(query)

    print(f"\n🔍 Query: {query}\n")
    print("=" * 60)

    for i, (doc, score) in enumerate(results):
        print(f"\n[Rank {i+1}] Similarity: {score:.3f}")
        print(f"Source: {doc.metadata.get('source', 'unknown')}")
        print(f"Content: {doc.page_content[:200]}...")
        print("-" * 40)

# ── Always test retrieval BEFORE adding the LLM ──
# If retrieved chunks are wrong, LLM can't give right answers.
# Fix retrieval first, then add generation.