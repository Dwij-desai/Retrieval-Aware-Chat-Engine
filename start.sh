#!/bin/bash
# ── AI SaaS Chatbot — Start Script ───────────────────────────────
# Usage: bash start.sh
# Starts the FastAPI server using the AI_SaaS conda environment.
# Auto-ingests data/ into ChromaDB if the vector store is empty.

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

export PYTHONPATH="$DIR"

PYTHON="/opt/anaconda3/envs/AI_SaaS/bin/python"

echo ""
echo "🤖 AI SaaS Chatbot — Starting..."
echo "📂 Project root : $DIR"
echo "🐍 Python       : $($PYTHON --version)"
echo ""

# ── Auto-ingest if chroma_db is missing or empty ─────────────────
CHROMA_DIR="$DIR/chroma_db"
if [ ! -d "$CHROMA_DIR" ] || [ -z "$(ls -A "$CHROMA_DIR" 2>/dev/null)" ]; then
  echo "📥 ChromaDB not found — running ingestion from data/..."
  "$PYTHON" backend/ingest.py
  echo ""
else
  echo "✅ ChromaDB already populated — skipping ingestion."
  echo ""
fi

echo "🌐 API URL  : http://127.0.0.1:8000"
echo "📖 Docs URL : http://127.0.0.1:8000/docs"
echo ""

"$PYTHON" -m uvicorn backend.api:app --reload --port 8000 --host 0.0.0.0
