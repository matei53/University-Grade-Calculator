#!/bin/bash
# Run tests and quality checks for the entire project

set -e  # Exit on first error

echo "=========================================="
echo "University Grade Calculator - Test Suite"
echo "=========================================="
echo

echo "📦 Checking dependencies..."
if ! python -m pip show pytest > /dev/null; then
    echo "Installing test dependencies..."
    python -m pip install -q -r server/requirements.txt
fi

echo
echo "🧹 Running code quality checks..."
echo

echo "1️⃣  Checking imports with isort..."
isort --check-only . --skip=venv,.git || true

echo "2️⃣  Checking formatting with black..."
black --check . --exclude=venv,.git || true

echo "3️⃣  Running linter (flake8)..."
flake8 . --ignore=migrations || true

echo "4️⃣  Type checking with mypy (server)..."
mypy server || true

echo
echo "✅ Running tests..."
echo

pytest server/tests/ -v --cov=server --cov-report=html --cov-report=term-missing

echo
echo "=========================================="
echo "✨ All tests completed!"
echo "📊 Coverage report: htmlcov/index.html"
echo "=========================================="
