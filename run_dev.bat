@echo off
cd /d "%~dp0"
echo ========================================================
echo           Starting CredVista Development Servers
echo ========================================================
echo 1. Starting FastAPI backend on http://127.0.0.1:8000 ...
start "CredVista Backend" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo 2. Starting Vite frontend on http://localhost:5173 ...
start "CredVista Frontend" cmd /k "cd frontend && npm run dev"

echo Done. Open http://localhost:5173 in your browser.
