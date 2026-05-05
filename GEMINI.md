# AI SaaS Chatbot Repository Guidelines

## Project Context
This project is a Retrieval-Augmented Generation (RAG) system for an AI SaaS chatbot. It uses Google Gemini as the primary LLM, LangChain for orchestration, and ChromaDB for local vector storage.

Key technologies:
- LLM: `gemini-1.5-flash` via `langchain-google-genai`
- Orchestration: `LangChain`
- Vector database: `ChromaDB` (local persistence)
- Data processing: `pandas` and `openpyxl`
- Configuration: `Pydantic Settings`

## Project Structure & Module Organization
Core application code lives in `backend/`:
- `backend/config.py`: environment-driven settings (`GOOGLE_API_KEY`, chunking, retrieval, model config).
- `backend/ingest.py`: multi-format document loading (PDF, TXT, CSV, Excel, JSON), chunking, and ingestion flow.
- `backend/embedder.py`: embedding model selection (local HuggingFace or Google embeddings).

Data and docs:
- `data/`: local input files used by ingestion runs.
- `docs/`: project documentation and guides.
- `docs/explanation.md`: detailed technical walkthrough.
- `docs/AGENTS.md`: synchronization instructions.
- `GEMINI.md`: repository guidelines (this file).
- `Test_dataset/`: larger sample datasets for manual validation.
- `learning/Vector-Database/`: reference guides and learning material.

## Build, Test, and Development Commands
- `bash scripts/Environment.sh`  
  Creates/activates `ai_saas` Conda env and installs dependencies.
- `bash scripts/start.sh`  
  Main entry point to start the API and auto-ingest data.
- `conda env create -f environment.yml && conda activate ai_saas`  
  Reproducible environment setup from config.
- `export PYTHONPATH=$PYTHONPATH:$(pwd)/backend`  
  Required so scripts can import `config`.
- `python backend/ingest.py`  
  Runs ingestion + chunking smoke test against `./data`.
- `python backend/embedder.py`  
  Verifies embedding generation and prints vector info.
- `python3 -m py_compile backend/*.py`  
  Quick syntax validation before committing.

## Configuration
The system expects a `GOOGLE_API_KEY` in environment variables or in a root `.env` file.

- Required variable: `GOOGLE_API_KEY`
- Optional overrides: `CHROMA_PERSIST_DIR`, `COLLECTION_NAME`, `MODEL_NAME`, and related settings in `backend/config.py`

## Coding Style & Development Conventions
Use Python 3.11 conventions:
- 4-space indentation
- `snake_case` for functions/variables
- `PascalCase` for classes

Project conventions:
- Configuration first: manage global settings and secrets through `backend/config.py`.
- Deterministic RAG defaults: keep low temperature settings for factual consistency.
- Smart splitting: preserve sentence integrity when chunking (for example with `RecursiveCharacterTextSplitter`).
- Explicit format handling: keep readable branches/loaders for each file type.
- Stable metadata keys: keep keys such as `source`, `row`, and `item` consistent for retrieval and debugging.
- Add short docstrings for non-trivial functions.

## Testing Guidelines
There is no formal `tests/` suite yet. For each change:
- Run targeted smoke checks.
- Include exact validation commands in PR notes.

If you add automated tests:
- Use `pytest` naming (`tests/test_<module>.py`).
- Cover ingestion edge cases (empty files, unsupported types, malformed JSON).

## Commit & Pull Request Guidelines
This workspace snapshot has no Git history metadata, so follow Conventional Commit style:
- `feat: add json loader in ingest pipeline`
- `fix: guard against empty chunk list`

Keep commits atomic (one logical change each). PRs should include:
- Purpose
- Changed files
- Validation commands
- Short before/after behavior summary

## Security & Configuration Tips
- Store secrets in `.env` (especially `GOOGLE_API_KEY`) and never commit them.
- Prefer local embeddings (`use_google=False`) for offline or development work.
- Do not commit generated vector stores unless explicitly required.

## Roadmap
- [ ] Implement vector embedding storage logic in `ingest.py`.
- [ ] Create a FastAPI `api.py` to expose retrieval and chat endpoints.
- [ ] Add a frontend for interacting with the chatbot.
- [ ] Integrate session management for multi-user chat history.
