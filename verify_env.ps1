# verify_env.ps1
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Chrona - Environment Verification" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0

# Check Node.js
try {
    $nodeVersion = node -v 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Node.js found: $nodeVersion" -ForegroundColor Green
    } else {
        throw "Node.js not found"
    }
} catch {
    Write-Host "[ERROR] Node.js is not installed or not in PATH." -ForegroundColor Red
    $errors++
}

# Check Python
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "[ERROR] Python 3.11+ is not installed or not in PATH." -ForegroundColor Red
    $errors++
}

# Check Docker
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker found: $dockerVersion" -ForegroundColor Green
    } else {
        throw "Docker not found"
    }
} catch {
    Write-Host "[ERROR] Docker Desktop is not installed or not running." -ForegroundColor Red
    $errors++
}

Write-Host ""
if ($errors -eq 0) {
    Write-Host "✅ All dependencies are installed! Environment is ready for Phase 2." -ForegroundColor Green
} else {
    Write-Host "❌ Please install missing dependencies before proceeding." -ForegroundColor Red
}
Write-Host "==========================================" -ForegroundColor Cyan