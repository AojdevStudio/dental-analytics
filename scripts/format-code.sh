#!/usr/bin/env bash
# Code formatting script for dental analytics project
# Automatically formats all Python code with Black and Ruff

set -e

echo "🎨 Auto-formatting code for dental analytics..."
echo "======================================"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🖤 Running Black formatter..."
uv run black backend/ frontend/ tests/ test_calculations.py
echo -e "${GREEN}✅ Black formatting complete${NC}"

echo ""
echo "🔧 Running Ruff auto-fixes..."
uv run ruff check --fix backend/ frontend/ tests/ test_calculations.py
echo -e "${GREEN}✅ Ruff fixes applied${NC}"

echo ""
echo -e "${GREEN}🎉 Code formatting complete!${NC}"
echo "Run 'scripts/quality-check.sh' to verify all quality standards."
echo "======================================"
