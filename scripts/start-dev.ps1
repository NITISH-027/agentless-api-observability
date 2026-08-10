# PowerShell script to spin up both frontend and backend dev servers
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Starting Development Servers" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

Write-Host "🚀 Launching FastAPI backend server at http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Starting FastAPI Backend...'; cd backend; .venv\Scripts\uvicorn app.main:app --reload --port 8000"

Write-Host "🚀 Launching Next.js frontend dashboard at http://127.0.0.1:3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Starting Next.js Frontend...'; cd frontend; npm run dev"

Write-Host ""
Write-Host "Both servers launched in separate background terminal windows." -ForegroundColor Yellow
