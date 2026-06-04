# Run tests and quality checks for the entire project
# PowerShell script for Windows

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "University Grade Calculator - Test Suite" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
$pipCheck = python -m pip show pytest 2>$null
if (-not $pipCheck) {
    Write-Host "Installing test dependencies..." -ForegroundColor Yellow
    python -m pip install -q -r server/requirements.txt
}

Write-Host ""
Write-Host "🧹 Running code quality checks..." -ForegroundColor Yellow
Write-Host ""

Write-Host "1️⃣  Checking imports with isort..." -ForegroundColor Magenta
isort --check-only . --skip=venv,.git 2>$null; $null

Write-Host "2️⃣  Checking formatting with black..." -ForegroundColor Magenta
black --check . --exclude=venv,.git 2>$null; $null

Write-Host "3️⃣  Running linter (flake8)..." -ForegroundColor Magenta
flake8 . --ignore=migrations 2>$null; $null

Write-Host "4️⃣  Type checking with mypy (server)..." -ForegroundColor Magenta
mypy server 2>$null; $null

Write-Host ""
Write-Host "✅ Running tests..." -ForegroundColor Green
Write-Host ""

pytest server/tests/ -v --cov=server --cov-report=html --cov-report=term-missing

Write-Host ""
Write-Host "===========================================" -ForegroundColor Green
Write-Host "✨ All tests completed!" -ForegroundColor Green
Write-Host "📊 Coverage report: htmlcov/index.html" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Green
