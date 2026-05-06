#!/bin/bash
# Test runner script with various options

set -e

echo "🧪 AI SaaS Chatbot Test Suite"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
TEST_MODE="${1:-all}"
VERBOSE="${2:-}"

# Run pytest with appropriate options
run_tests() {
    case "$TEST_MODE" in
        all)
            echo "Running all tests..."
            pytest $VERBOSE
            ;;
        unit)
            echo "Running unit tests..."
            pytest -m unit $VERBOSE
            ;;
        integration)
            echo "Running integration tests..."
            pytest -m integration $VERBOSE
            ;;
        smoke)
            echo "Running smoke tests..."
            pytest -m smoke $VERBOSE
            ;;
        coverage)
            echo "Running tests with coverage..."
            pytest --cov=backend --cov-report=html --cov-report=term-missing $VERBOSE
            echo ""
            echo "✅ Coverage report generated: htmlcov/index.html"
            ;;
        fast)
            echo "Running fast tests (excluding slow)..."
            pytest -m "not slow" $VERBOSE --tb=short
            ;;
        watch)
            echo "Running tests in watch mode..."
            if command -v ptw &> /dev/null; then
                ptw
            else
                echo "❌ pytest-watch not installed"
                echo "Install with: pip install pytest-watch"
                exit 1
            fi
            ;;
        debug)
            echo "Running tests with debugger..."
            pytest --pdb -x $VERBOSE
            ;;
        parallel)
            echo "Running tests in parallel..."
            if command -v pytest &> /dev/null; then
                pytest -n auto $VERBOSE
            else
                echo "❌ pytest-xdist not installed"
                echo "Install with: pip install pytest-xdist"
                exit 1
            fi
            ;;
        lint)
            echo "Syntax check..."
            python3 -m py_compile backend/*.py
            echo "✅ All files compile successfully"
            ;;
        *)
            echo "❌ Unknown test mode: $TEST_MODE"
            echo ""
            echo "Usage: bash scripts/test.sh [mode] [verbose]"
            echo ""
            echo "Modes:"
            echo "  all          - Run all tests (default)"
            echo "  unit         - Run unit tests only"
            echo "  integration  - Run integration tests only"
            echo "  smoke        - Run smoke tests only"
            echo "  coverage     - Generate coverage report"
            echo "  fast         - Run fast tests (exclude slow)"
            echo "  watch        - Watch mode (requires pytest-watch)"
            echo "  debug        - Interactive debugging"
            echo "  parallel     - Run tests in parallel"
            echo "  lint         - Syntax check only"
            echo ""
            echo "Options:"
            echo "  verbose      - Add -v flag for verbose output"
            echo ""
            echo "Examples:"
            echo "  bash scripts/test.sh              # Run all tests"
            echo "  bash scripts/test.sh unit         # Run unit tests"
            echo "  bash scripts/test.sh coverage     # Generate coverage"
            echo "  bash scripts/test.sh all verbose  # Verbose output"
            exit 1
            ;;
    esac
}

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not found"
    echo "Install with: pip install pytest"
    exit 1
fi

# Add verbose flag if requested
if [ "$VERBOSE" = "verbose" ]; then
    VERBOSE="-vv"
else
    VERBOSE=""
fi

# Run tests
run_tests

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Tests passed!${NC}"
else
    echo -e "${RED}❌ Tests failed!${NC}"
fi

exit $exit_code
