# Step-5: Expanded Pytest Coverage

## Overview
Comprehensive automated testing for the RAG pipeline ensures reliability, catches regressions, and enables confident refactoring.

## Test Suite Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest settings
├── test_ingest.py           # Ingestion pipeline tests
├── test_rag_engine.py       # RAG engine and chain tests
└── test_integration.py      # End-to-end integration tests
```

## Quick Start

### 1. Install Test Dependencies
```bash
pip install pytest pytest-cov pytest-timeout pytest-mock
```

### 2. Run All Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_ingest.py

# Run specific test
pytest tests/test_ingest.py::TestPDFLoading::test_load_valid_pdf
```

### 3. Run Tests by Category
```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Only tests requiring API keys
pytest -m requires_api_key
```

## Test Categories

### Unit Tests
Fast, isolated tests of individual components.

**Files:** `test_ingest.py`, `test_rag_engine.py`

**Examples:**
- PDF loading
- Text splitting
- CSV parsing
- Error handling

**Run:** `pytest -m unit`

### Integration Tests
Test interactions between components.

**File:** `test_integration.py`

**Examples:**
- Full ingestion pipeline
- RAG chain end-to-end
- Vector store + retrieval
- Multi-provider fallback

**Run:** `pytest -m integration`

### Smoke Tests
Quick sanity checks (< 1s each).

**Run:** `pytest -m smoke`

## Coverage Report

### Generate HTML Coverage Report
```bash
pytest --cov=backend --cov-report=html

# Open report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

### View Terminal Report
```bash
pytest --cov=backend --cov-report=term-missing
```

### Coverage Targets
- Overall: ≥ 70%
- Critical paths: ≥ 85%
- Error handling: 100%

## Test Files Overview

### test_ingest.py
Tests the data ingestion pipeline.

**Classes:**
- `TestPDFLoading`: PDF document loading
- `TestTextLoading`: Plain text loading
- `TestCSVLoading`: CSV parsing
- `TestJSONLoading`: JSON parsing
- `TestIngestionPipeline`: Full pipeline
- `TestErrorHandling`: Error scenarios
- `TestDocumentMetadata`: Metadata preservation

**Key Tests:**
```python
# Test PDF handling
test_load_valid_pdf()
test_load_empty_pdf()
test_load_corrupted_pdf()

# Test CSV handling
test_load_valid_csv()
test_load_malformed_csv()
test_load_csv_with_special_chars()

# Test full pipeline
test_ingest_multiple_formats()
test_ingest_large_file()
test_ingest_ignores_hidden_files()
```

### test_rag_engine.py
Tests RAG chain and LLM interaction.

**Classes:**
- `TestRAGChainConstruction`: Chain building
- `TestContextRetrieval`: Document retrieval
- `TestPromptFormatting`: Prompt assembly
- `TestErrorHandling`: Error scenarios
- `TestMultiProviderFallback`: Provider switching
- `TestAskFunctionality`: Main ask() function
- `TestResponseQuality`: Output validation
- `TestLatencyTracking`: Performance metrics

**Key Tests:**
```python
# Test chain construction
test_build_chain_with_groq()
test_build_chain_with_gemini()

# Test retrieval
test_retrieve_context_basic()
test_retrieve_no_results()

# Test error handling
test_quota_exceeded_error()
test_model_unavailable_error()

# Test fallback
test_fallback_on_primary_failure()
test_should_retry_on_quota()

# Test ask function
test_ask_returns_string()
test_ask_with_history()
test_ask_raises_on_no_models()
```

## Fixtures (conftest.py)

### Common Fixtures
```python
@pytest.fixture
def data_dir(tmp_path):
    """Temporary data directory"""

@pytest.fixture
def mock_vector_store():
    """Mock ChromaDB vector store"""

@pytest.fixture
def sample_document():
    """Single sample document"""

@pytest.fixture
def sample_documents():
    """Multiple sample documents"""

@pytest.fixture
def chat_history():
    """Sample multi-turn conversation"""

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
```

### Using Fixtures
```python
def test_with_fixture(data_dir, sample_documents):
    # data_dir is a temporary directory
    # sample_documents is a list of Document objects
    pass
```

## Running Tests Locally

### Development Workflow
```bash
# Watch mode - re-run tests on file changes
ptw  # requires pytest-watch: pip install pytest-watch

# Run tests in parallel
pytest -n auto  # requires pytest-xdist: pip install pytest-xdist

# Run with coverage
pytest --cov=backend --cov-report=term-missing
```

### Before Committing
```bash
# Run all tests
pytest

# Check coverage
pytest --cov=backend --cov-report=term

# Ensure no warnings
pytest -W error::DeprecationWarning
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=backend
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Writing New Tests

### Template for Ingestion Tests
```python
def test_load_new_format(tmp_path):
    """Test loading a new file format."""
    # Setup
    file_path = tmp_path / "test.newformat"
    file_path.write_text("content")
    
    # Execute
    docs = load_new_format(str(file_path))
    
    # Assert
    assert len(docs) > 0
    assert "content" in docs[0].page_content
```

### Template for RAG Engine Tests
```python
@patch('backend.rag_engine.build_rag_chain')
def test_rag_behavior(mock_build_chain):
    """Test RAG engine behavior."""
    # Setup mock
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = "Expected response"
    mock_build_chain.return_value = mock_chain
    
    # Execute
    result = ask("Test question")
    
    # Assert
    assert result == "Expected response"
    mock_chain.invoke.assert_called_once()
```

## Debugging Failed Tests

### View Test Details
```bash
# Show full tracebacks
pytest -vv

# Show local variables in tracebacks
pytest -l

# Drop into pdb on failure
pytest --pdb

# Show print statements
pytest -s
```

### Common Issues

**Test imports fail:**
```bash
# Check PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest
```

**Tests pass locally but fail in CI:**
- Check environment variables
- Verify file paths (use tmp_path fixture)
- Check for timezone-dependent tests
- Ensure no hardcoded paths

**Tests are slow:**
- Mark slow tests: `@pytest.mark.slow`
- Run with `pytest -m "not slow"`
- Consider mocking external API calls
- Profile with: `pytest --profile`

## Best Practices

### 1. Test Naming
```python
# ✅ Good: Clear what is being tested
def test_load_valid_pdf():
    pass

# ❌ Bad: Vague
def test_pdf():
    pass
```

### 2. Arrange-Act-Assert Pattern
```python
def test_example():
    # Arrange: Set up test data
    test_file = create_test_file()
    
    # Act: Perform the action
    result = load_file(test_file)
    
    # Assert: Verify the result
    assert result is not None
```

### 3. Use Fixtures for Setup
```python
# ❌ Don't: Duplicate setup
def test_1(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content")

def test_2(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content")

# ✅ Do: Create fixture
@pytest.fixture
def test_file(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content")
    return file

def test_1(test_file):
    pass

def test_2(test_file):
    pass
```

### 4. Mock External Calls
```python
# ❌ Don't: Call real APIs in tests
def test_rag():
    result = ask("question")  # Calls real LLM

# ✅ Do: Mock external dependencies
@patch('backend.rag_engine.build_rag_chain')
def test_rag(mock_chain):
    mock_chain.return_value.invoke.return_value = "Answer"
    result = ask("question")
    assert result == "Answer"
```

## Coverage Goals

| Component | Target | Status |
|-----------|--------|--------|
| ingest.py | 80% | ⏳ In progress |
| rag_engine.py | 85% | ⏳ In progress |
| config.py | 70% | ⏳ In progress |
| vector_store.py | 75% | ⏳ In progress |
| **Overall** | **75%** | ⏳ In progress |

## Next Steps

1. ✅ Step-2: Ragas Evaluation
2. ✅ Step-3: LangSmith Tracing
3. ✅ Step-4: Automated Ingestion
4. ✅ Step-5: Expanded pytest Coverage

## Production Readiness Checklist

- ✅ Docker containerization
- ✅ Evaluation framework
- ✅ Observability/tracing
- ✅ Automated ingestion
- ✅ Comprehensive tests
- [ ] API documentation
- [ ] Security audit
- [ ] Performance benchmarks
- [ ] Deployment playbook
