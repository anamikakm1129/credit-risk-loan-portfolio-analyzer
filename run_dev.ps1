# CredVista Local Development Runner
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "      Starting CredVista Credit Risk Platform           " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Start FastAPI backend
Write-Host "Starting FastAPI backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

# Start Vite React frontend
Write-Host "Starting Vite React frontend on http://localhost:5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location frontend; npm run dev"

Write-Host "`nBoth services launched! Open http://localhost:5173 in your browser." -ForegroundColor Cyan
