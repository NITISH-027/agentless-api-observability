# PowerShell script to verify the entire platform codebase
$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Running Backend Python Test Suite" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Push-Location backend
& .venv\Scripts\pytest
Pop-Location

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Compiling Frontend Next.js Build" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Push-Location frontend
npm run build
Pop-Location

Write-Host ""
Write-Host "✅ Verification Complete!" -ForegroundColor Green
