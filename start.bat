@echo off
title EduMind AI Launcher
echo ======================================================================
echo              Starting EduMind AI Full-Stack Platform
echo ======================================================================
echo.
echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000...
start "EduMind Backend" cmd /k "py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak > nul

echo [2/2] Launching Vite React Frontend on http://localhost:3000...
start "EduMind Frontend" cmd /k "npm.cmd run dev"

echo.
echo ======================================================================
echo  EduMind AI is now running!
echo  - Frontend Web App:  http://localhost:3000
echo  - Backend API:       http://127.0.0.1:8000
echo  - API Swagger Docs:  http://127.0.0.1:8000/docs
echo ======================================================================
echo.
pause
