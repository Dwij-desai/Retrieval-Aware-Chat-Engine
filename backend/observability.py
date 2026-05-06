"""
LangSmith Integration for RAG Pipeline Observability

LangSmith provides:
- Tracing: See exactly what was retrieved, what prompt was used, LLM response
- Debugging: Inspect execution traces to find bottlenecks
- Monitoring: Track performance metrics over time
- Logging: Store all interactions for later analysis

Setup:
1. Create account at https://smith.langchain.com
2. Get API key from settings
3. Set LANGCHAIN_API_KEY environment variable
4. Enable tracing with enable_langsmith_tracing()
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def enable_langsmith_tracing(project_name: str = "ai-saas-chatbot"):
    """
    Enable LangSmith tracing for all LangChain operations.
    
    Args:
        project_name: Project name in LangSmith dashboard
    
    Environment Variables Required:
        LANGCHAIN_API_KEY: Your LangSmith API key
        LANGCHAIN_TRACING_V2: Should be "true"
    
    Example:
        enable_langsmith_tracing("my-project")
        # Now all RAG operations are traced
    """
    try:
        api_key = os.getenv("LANGCHAIN_API_KEY")
        if not api_key:
            logger.warning(
                "LANGCHAIN_API_KEY not set. LangSmith tracing disabled. "
                "Set it to enable tracing: export LANGCHAIN_API_KEY=your_key"
            )
            return False

        # Enable LangSmith
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project_name

        logger.info(f"✅ LangSmith tracing enabled (project: {project_name})")
        logger.info(f"   Dashboard: https://smith.langchain.com/projects/{project_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to enable LangSmith: {e}")
        return False


def log_rag_run(
    question: str,
    retrieved_docs: list,
    generated_answer: str,
    model: str,
    latency_ms: float,
    metadata: Optional[dict] = None,
):
    """
    Log a complete RAG run to LangSmith.
    
    This is called automatically when using the RAG engine with
    LangSmith enabled. Manual calls are only needed for custom logging.
    
    Args:
        question: User's question
        retrieved_docs: List of retrieved document chunks
        generated_answer: LLM-generated answer
        model: Which LLM was used (e.g., "groq", "gemini")
        latency_ms: Response time in milliseconds
        metadata: Optional additional data
    """
    from langsmith import Client

    try:
        client = Client()
        
        run_data = {
            "name": "RAG Query",
            "inputs": {
                "question": question,
                "retrieved_docs": retrieved_docs,
            },
            "outputs": {
                "answer": generated_answer,
                "model": model,
                "latency_ms": latency_ms,
            },
            "metadata": metadata or {},
        }
        
        client.create_run(
            name="RAG Query",
            run_type="chain",
            inputs=run_data["inputs"],
            outputs=run_data["outputs"],
            metadata=run_data["metadata"],
        )
        
        logger.debug("RAG run logged to LangSmith")
        return True
        
    except Exception as e:
        logger.debug(f"Could not log to LangSmith: {e}")
        return False


def disable_langsmith_tracing():
    """Disable LangSmith tracing."""
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_PROJECT", None)
    logger.info("LangSmith tracing disabled")


# Auto-enable if API key is present
if os.getenv("LANGCHAIN_API_KEY"):
    enable_langsmith_tracing()
