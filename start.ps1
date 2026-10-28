# EduMind AI PowerShell Launcher
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "             Starting EduMind AI Full-Stack Platform" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Vite React Frontend on http://localhost:3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm.cmd run dev"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " EduMind AI is running:" -ForegroundColor Green
Write-Host " - Frontend Web App:  http://localhost:3000" -ForegroundColor White
Write-Host " - Backend API:       http://127.0.0.1:8000" -ForegroundColor White
Write-Host " - API Docs:          http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
