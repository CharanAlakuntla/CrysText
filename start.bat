@echo off
echo ============================================
echo  CrysText - Starting all services
echo ============================================

:: Create MongoDB data directory if missing
if not exist "C:\data\db" mkdir C:\data\db

:: Start MongoDB in a new window
echo [1/3] Starting MongoDB...
start "MongoDB" cmd /k ""C:\Program Files\MongoDB\Server\8.3\bin\mongod.exe" --dbpath C:\data\db"

:: Wait for MongoDB to start
timeout /t 4 /nobreak >nul

:: Start Backend in a new window
echo [2/3] Starting Backend API...
start "CrysText Backend" cmd /k "cd /d "%~dp0backend" && "%~dp0.venv\Scripts\uvicorn.exe" app.main:app --reload --port 8000"

:: Wait a moment
timeout /t 2 /nobreak >nul

:: Start Frontend in a new window
echo [3/3] Starting Frontend...
start "CrysText Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ============================================
echo  All services starting in separate windows
echo  App:      http://localhost:3000
echo  API:      http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo ============================================
echo.
pause
