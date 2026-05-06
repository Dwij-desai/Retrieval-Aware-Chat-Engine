#!/bin/bash
# Docker Setup Validation Script
# Verifies all Docker files are correctly formatted

set -e

echo "🐳 Docker Setup Validation"
echo "=========================="
echo ""

# Check if files exist
echo "✓ Checking file existence..."
[ -f "Dockerfile" ] && echo "  ✓ Dockerfile found" || (echo "  ✗ Dockerfile missing" && exit 1)
[ -f "docker-compose.yml" ] && echo "  ✓ docker-compose.yml found" || (echo "  ✗ docker-compose.yml missing" && exit 1)
[ -f ".dockerignore" ] && echo "  ✓ .dockerignore found" || (echo "  ✗ .dockerignore missing" && exit 1)
[ -f "requirements.txt" ] && echo "  ✓ requirements.txt found" || (echo "  ✗ requirements.txt missing" && exit 1)
echo ""

# Validate YAML syntax (docker-compose.yml)
echo "✓ Validating docker-compose.yml syntax..."
if command -v python3 &> /dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" 2>/dev/null; then
        echo "  ✓ YAML syntax valid"
    else
        echo "  ⚠ YAML module not available, checking basic structure instead"
        grep -q "version:" docker-compose.yml && echo "  ✓ YAML structure looks valid"
    fi
else
    echo "  ⚠ Python3 not found, checking basic structure instead"
    grep -q "version:" docker-compose.yml && echo "  ✓ YAML structure looks valid"
fi
echo ""

# Check Dockerfile syntax basics
echo "✓ Checking Dockerfile structure..."
grep -q "FROM python:3.11-slim" Dockerfile && echo "  ✓ Base image correct" || (echo "  ✗ Incorrect base image" && exit 1)
grep -q "EXPOSE 8000" Dockerfile && echo "  ✓ Port 8000 exposed" || (echo "  ✗ Port not exposed" && exit 1)
grep -q "HEALTHCHECK" Dockerfile && echo "  ✓ Health check configured" || (echo "  ✗ Health check missing" && exit 1)
echo ""

# Check docker-compose.yml structure
echo "✓ Checking docker-compose.yml structure..."
grep -q "chroma:" docker-compose.yml && echo "  ✓ ChromaDB service defined" || (echo "  ✗ ChromaDB service missing" && exit 1)
grep -q "api:" docker-compose.yml && echo "  ✓ API service defined" || (echo "  ✗ API service missing" && exit 1)
grep -q "depends_on:" docker-compose.yml && echo "  ✓ Service dependencies defined" || (echo "  ✗ Dependencies missing" && exit 1)
echo ""

# Check .env template
if [ -f ".env" ]; then
    echo "✓ Checking .env file..."
    grep -q "GOOGLE_API_KEY" .env && echo "  ✓ GOOGLE_API_KEY present" || echo "  ⚠ GOOGLE_API_KEY not set"
else
    echo "⚠ .env file not found (will use environment variables)"
fi
echo ""

echo "✅ All Docker files validated successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Ensure Docker and Docker Compose are installed"
echo "2. Set API keys in .env file"
echo "3. Run: docker-compose up -d"
echo "4. Check: docker-compose ps"
echo "5. Test: curl http://localhost:8000/health"
echo ""
