#!/usr/bin/env bash
# Quick test script for dental analytics project
# Runs essential tests without full coverage

set -e

echo "⚡ Quick test run for dental analytics..."
echo "======================================"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Function to print colored status
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1 PASSED${NC}"
    else
        echo -e "${RED}❌ $1 FAILED${NC}"
        exit 1
    fi
}

echo "🧪 Running pytest (fast, no coverage)..."
uv run pytest tests/ -v --tb=short
print_status "Unit tests"

echo ""
echo "📊 Verifying manual calculations..."
uv run python test_calculations.py > /dev/null 2>&1
print_status "Manual calculations"

echo ""
echo -e "${GREEN}⚡ Quick tests passed!${NC}"
echo "For full quality checks, run: scripts/quality-check.sh"
echo "======================================"
