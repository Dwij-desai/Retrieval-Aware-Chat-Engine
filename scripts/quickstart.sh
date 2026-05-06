#!/bin/bash
# Quick reference guide for running the AI SaaS Chatbot
# Print this with: bash scripts/quickstart.sh

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════╗
║           🚀 AI SaaS Chatbot - Quick Start Commands                      ║
╚══════════════════════════════════════════════════════════════════════════╝

📋 OPTION 1: DOCKER (RECOMMENDED - 5 minutes)
─────────────────────────────────────────────────────────────────────────

  1️⃣  Validate setup:
      bash scripts/validate-docker.sh

  2️⃣  Set API keys in .env file:
      export GOOGLE_API_KEY=your_key
      export GROQ_API_KEY=your_key

  3️⃣  Start services:
      docker-compose up -d

  4️⃣  Verify running:
      docker-compose ps

  5️⃣  Test API:
      curl http://localhost:8000/health

  6️⃣  Open API docs:
      open http://localhost:8000/docs

  7️⃣  Stop services:
      docker-compose down


📋 OPTION 2: LOCAL DEVELOPMENT (Conda)
─────────────────────────────────────────────────────────────────────────

  1️⃣  Create conda environment:
      bash scripts/Environment.sh

  2️⃣  Configure .env:
      export GOOGLE_API_KEY=your_key
      export GROQ_API_KEY=your_key

  3️⃣  Ingest data (first time only):
      conda activate ai_saas
      python backend/ingest.py

  4️⃣  Start server:
      bash scripts/start.sh

  5️⃣  Test API:
      curl http://localhost:8000/health

  6️⃣  Open API docs:
      open http://localhost:8000/docs

  7️⃣  Stop server:
      Ctrl+C in terminal


🔍 VERIFY SETUP
─────────────────────────────────────────────────────────────────────────

  Check Health:
      curl http://localhost:8000/health

  Check ChromaDB:
      curl http://localhost:8001/api/v1

  View API Docs:
      open http://localhost:8000/docs

  Test Question:
      curl -X POST http://localhost:8000/ask \
        -H "Content-Type: application/json" \
        -d '{"question":"What is this?","chat_id":"test"}'


🧪 RUN TESTS
─────────────────────────────────────────────────────────────────────────

  All tests:
      pytest

  With coverage:
      pytest --cov=backend --cov-report=html

  Using test script:
      bash scripts/test.sh coverage


📊 EVALUATE QUALITY
─────────────────────────────────────────────────────────────────────────

  Run evaluation:
      python backend/evaluation.py

  View results:
      cat evaluation_report.json


🔍 ENABLE TRACING (LangSmith)
─────────────────────────────────────────────────────────────────────────

  Set API key:
      export LANGCHAIN_API_KEY=your_key

  Start services:
      docker-compose up -d
      # OR
      bash scripts/start.sh

  View dashboard:
      open https://smith.langchain.com/projects/ai-saas-chatbot


🤖 AUTO-INGEST DATA
─────────────────────────────────────────────────────────────────────────

  Watch mode (real-time):
      python backend/ingest_orchestrator.py --mode watch

  Scheduled (daily):
      python backend/ingest_orchestrator.py --mode schedule --interval daily

  One-time:
      python backend/ingest_orchestrator.py --mode once


📁 IMPORTANT DIRECTORIES
─────────────────────────────────────────────────────────────────────────

  Code:           ./backend/
  Data:           ./data/
  Vector DB:      ./chroma_db/
  Chat Memory:    ./chat_memory.db
  Tests:          ./tests/
  Docs:           ./docs/
  Configuration:  ./.env


📚 DOCUMENTATION
─────────────────────────────────────────────────────────────────────────

  Getting Started:       docs/HOW_TO_RUN.md (this file!)
  Docker Setup:          docs/DOCKER_SETUP.md
  Testing Guide:         docs/TESTING.md
  Evaluation:            docs/EVALUATION.md
  Observability:         docs/LANGSMITH.md
  Auto Ingestion:        docs/AUTO_INGEST.md
  Technical Details:     docs/explanation.md
  Architecture:          README.md


🆘 TROUBLESHOOTING
─────────────────────────────────────────────────────────────────────────

  API not responding?
      Check: docker-compose ps
      Logs:  docker-compose logs api

  Port 8000 in use?
      Kill:  lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
      Or:    Change port in docker-compose.yml

  Tests failing?
      Run verbose: pytest -vv
      Check paths: echo $PYTHONPATH

  Data not ingesting?
      Manual: docker-compose exec api python backend/ingest.py
      Watch:  python backend/ingest_orchestrator.py --mode watch


✅ QUICK CHECKLIST
─────────────────────────────────────────────────────────────────────────

  After starting, verify:
  ☐ docker-compose ps shows both services running
  ☐ curl http://localhost:8000/health returns 200 OK
  ☐ curl http://localhost:8001/api/v1 returns ChromaDB info
  ☐ http://localhost:8000/docs opens in browser
  ☐ Sample question returns an answer
  ☐ pytest runs without errors


💡 PRO TIPS
─────────────────────────────────────────────────────────────────────────

  • Use 'docker-compose logs -f' to watch real-time logs
  • Set LANGCHAIN_API_KEY to get full tracing in LangSmith
  • Run 'bash scripts/test.sh watch' for auto re-run on file changes
  • Check 'docs/MLOPS_SUMMARY.md' for complete system overview
  • Use '-v' flag with curl for more details on API responses


🚀 YOU'RE ALL SET!
─────────────────────────────────────────────────────────────────────────

  Choose your option above and start running.
  For detailed instructions, see: docs/HOW_TO_RUN.md

EOF
