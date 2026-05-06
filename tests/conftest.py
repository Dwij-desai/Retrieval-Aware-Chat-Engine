"""
Pytest configuration and fixtures.

This file is automatically loaded by pytest and provides:
- Common fixtures
- Configuration
- Hooks
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["PYTHONPATH"] = str(PROJECT_ROOT)


@pytest.fixture
def project_root():
    """Return project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def data_dir(tmp_path):
    """Provide a temporary data directory."""
    data = tmp_path / "data"
    data.mkdir()
    return data


@pytest.fixture
def chroma_temp_dir(tmp_path):
    """Provide a temporary ChromaDB directory."""
    chroma = tmp_path / "chroma_db"
    chroma.mkdir()
    return chroma


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Provide mock environment variables."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key-groq")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-google")
    monkeypatch.setenv("PROVIDER", "groq")
    monkeypatch.setenv("CHUNK_SIZE", "1000")
    monkeypatch.setenv("CHUNK_OVERLAP", "100")


def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marks tests requiring API keys"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Mark tests that require API keys
        if "api_key" in item.name.lower():
            item.add_marker(pytest.mark.requires_api_key)

        # Mark integration tests
        if item.fspath.stem.startswith("test_integration_"):
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def mock_vector_store():
    """Provide a mock vector store."""
    from unittest.mock import MagicMock
    store = MagicMock()
    store.similarity_search.return_value = [
        MagicMock(
            page_content="Test context",
            metadata={"source": "test.txt"}
        )
    ]
    return store


@pytest.fixture
def sample_document():
    """Provide a sample document."""
    from langchain_core.documents import Document
    return Document(
        page_content="This is sample document content.",
        metadata={"source": "sample.txt"}
    )


@pytest.fixture
def sample_documents():
    """Provide multiple sample documents."""
    from langchain_core.documents import Document
    return [
        Document(page_content="Document 1", metadata={"source": "doc1.txt"}),
        Document(page_content="Document 2", metadata={"source": "doc2.txt"}),
        Document(page_content="Document 3", metadata={"source": "doc3.txt"}),
    ]


@pytest.fixture
def chat_history():
    """Provide sample chat history."""
    return [
        ("What is this system?", "This is a RAG chatbot."),
        ("How does it work?", "It uses embeddings for retrieval."),
    ]


@pytest.fixture
def cleanup_temp_files(tmp_path):
    """Automatically cleanup temporary files after test."""
    yield tmp_path
    # Cleanup happens automatically with tmp_path


# Skip markers for conditional skipping
def pytest_runtest_setup(item):
    """Skip tests based on conditions."""
    requires_api_key = any(
        mark.name == "requires_api_key" for mark in item.iter_markers()
    )
    
    if requires_api_key:
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            pytest.skip("Requires GROQ_API_KEY or GOOGLE_API_KEY environment variable")
