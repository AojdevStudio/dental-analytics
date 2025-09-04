#!/usr/bin/env bash
# Quality check script for dental analytics project
# Runs all code quality tools in the correct order

set -e  # Exit on any error

echo "🔍 Running comprehensive quality checks for dental analytics..."
echo "======================================"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored status
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1 PASSED${NC}"
    else
        echo -e "${RED}❌ $1 FAILED${NC}"
        exit 1
    fi
}

echo "📋 Step 1: Code formatting with Black..."
uv run black --check backend/ frontend/ tests/ test_calculations.py
print_status "Black formatting"

echo ""
echo "🔧 Step 2: Linting with Ruff..."
uv run ruff check backend/ frontend/ tests/ test_calculations.py
print_status "Ruff linting"

echo ""
echo "🏷️  Step 3: Type checking with MyPy..."
uv run mypy backend/ test_calculations.py
print_status "MyPy type checking"

echo ""
echo "🧪 Step 4: Running pytest test suite..."
uv run pytest tests/ -v --cov=backend --cov=frontend
print_status "Pytest tests"

echo ""
echo "📊 Step 5: Manual calculations verification..."
uv run python test_calculations.py > /dev/null 2>&1
print_status "Manual calculations"

echo ""
echo -e "${GREEN}🎉 All quality checks passed! Code is ready for commit.${NC}"
echo "======================================"
