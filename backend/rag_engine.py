from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

try:
    # Package-style imports (e.g., `python -m backend.rag_engine`)
    from backend.vector_store import get_vector_store
    from backend.config import settings
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.vector_store", "backend.config"}:
        raise
    # Script-style imports (e.g., `python backend/rag_engine.py`)
    from vector_store import get_vector_store
    from config import settings

# ── 1. THE PROMPT TEMPLATE ──────────────────────────────────────
# This is where most developers get lazy. A good prompt makes
# the difference between a hallucinating bot and an accurate one.

SYSTEM_PROMPT = """
You are a knowledgeable and helpful AI assistant.
Your rules:
    1. Answer ONLY using the provided context below.
    2. If the answer is not in the context, say: "I don't have enough information to answer that accurately."
    3. Be concise. Cite context when possible.
    4. Never make up information.
Context: {context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}")
])

# ── 2. FORMAT RETRIEVED DOCS ────────────────────────────────────
def format_docs(docs: list[Document]) -> str:
    """
    Join retrieved chunks into a single context string.
    """
    return "\n\n---\n\n".join([doc.page_content for doc in docs])

# ── 3. BUILD THE RAG CHAIN ──────────────────────────────────────
def build_rag_chain():
    """
    Creates the full RAG chain using LangChain's LCEL syntax.
    Chain: query → retriever → format → prompt → LLM → parse
    """
    vectorstore = get_vector_store()

    # Retriever: wraps vector store for easy use in chains
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.top_k}
    )

    # LLM: Gemini 1.5 Flash — free tier, fast, handles long contexts well
    # temperature=0.1 → more factual, less creative
    llm = ChatGoogleGenerativeAI(
        model=settings.model_name,  # "gemini-1.5-flash"
        temperature=settings.temperature,
        google_api_key=settings.google_api_key,
        convert_system_message_to_human=True  # required for Gemini
    )

    # LCEL Chain: connects each step with pipe operator |
    rag_chain = (
        {
            "context": retriever | format_docs,  # retrieves + formats
            "question": RunnablePassthrough()    # passes query through
        }
        | prompt              # fills the template
        | llm                 # sends to LLM
        | StrOutputParser()   # extracts text from response
    )
    return rag_chain

# ── 4. MAIN ASK FUNCTION ────────────────────────────────────────
def ask(question: str) -> str:
    """
    Single entry point for the RAG chatbot.
    """
    chain = build_rag_chain()
    # This chain expects a raw question string as input.
    return chain.invoke(question)

if __name__ == "__main__":
    answer = ask("What are the side effects of ibuprofen?")
    print(f"\n🤖 Answer:\n{answer}")
