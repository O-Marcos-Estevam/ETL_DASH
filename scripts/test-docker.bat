@echo off
REM ============================================
REM Docker Test Script - ETL Dashboard
REM ============================================
REM Tests Docker configuration and builds
REM Usage: test-docker.bat [build|validate|full]
REM ============================================

setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0.."
set "TEST_MODE=%~1"
if "%TEST_MODE%"=="" set "TEST_MODE=validate"

echo.
echo ============================================
echo   Docker Test - ETL Dashboard
echo   Mode: %TEST_MODE%
echo ============================================
echo.

REM Check if Docker is installed
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://docker.com
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker daemon is not running
    echo Please start Docker Desktop
    exit /b 1
)

echo [OK] Docker is installed and running
echo.

REM ============================================
REM Validate Docker files exist
REM ============================================
echo --- Validating Docker files ---

set "MISSING_FILES=0"

if not exist "%ROOT_DIR%\docker-compose.yml" (
    echo [ERROR] Missing: docker-compose.yml
    set "MISSING_FILES=1"
) else (
    echo [OK] docker-compose.yml exists
)

if not exist "%ROOT_DIR%\backend\Dockerfile" (
    echo [ERROR] Missing: backend/Dockerfile
    set "MISSING_FILES=1"
) else (
    echo [OK] backend/Dockerfile exists
)

if not exist "%ROOT_DIR%\frontend\Dockerfile" (
    echo [ERROR] Missing: frontend/Dockerfile
    set "MISSING_FILES=1"
) else (
    echo [OK] frontend/Dockerfile exists
)

if not exist "%ROOT_DIR%\frontend\nginx.conf" (
    echo [ERROR] Missing: frontend/nginx.conf
    set "MISSING_FILES=1"
) else (
    echo [OK] frontend/nginx.conf exists
)

if not exist "%ROOT_DIR%\.env.example" (
    echo [ERROR] Missing: .env.example
    set "MISSING_FILES=1"
) else (
    echo [OK] .env.example exists
)

if %MISSING_FILES% equ 1 (
    echo.
    echo [FAILED] Some Docker files are missing
    exit /b 1
)

echo.
echo [PASSED] All Docker files present
echo.

REM ============================================
REM Validate docker-compose syntax
REM ============================================
echo --- Validating docker-compose.yml syntax ---

cd /d "%ROOT_DIR%"
docker compose config >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] docker-compose.yml has syntax errors
    docker compose config
    exit /b 1
)

echo [OK] docker-compose.yml syntax is valid
echo.

REM Exit if only validating
if "%TEST_MODE%"=="validate" (
    echo ============================================
    echo   VALIDATION PASSED
    echo ============================================
    exit /b 0
)

REM ============================================
REM Build containers (if build or full mode)
REM ============================================
echo --- Building Docker images ---
echo This may take a few minutes...
echo.

REM Create .env if not exists
if not exist "%ROOT_DIR%\.env" (
    echo Creating .env from .env.example...
    copy "%ROOT_DIR%\.env.example" "%ROOT_DIR%\.env" >nul
)

docker compose build --no-cache
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Docker build failed
    exit /b 1
)

echo.
echo [OK] Docker images built successfully
echo.

REM Exit if only building
if "%TEST_MODE%"=="build" (
    echo ============================================
    echo   BUILD PASSED
    echo ============================================
    exit /b 0
)

REM ============================================
REM Full test - start containers and test
REM ============================================
echo --- Starting containers ---

docker compose up -d
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to start containers
    exit /b 1
)

echo Waiting for services to be healthy (30s)...
timeout /t 30 /nobreak >nul

REM Test backend health
echo.
echo --- Testing backend health ---
curl -s -o nul -w "%%{http_code}" http://localhost:4001/api/health > "%TEMP%\health_code.txt"
set /p HEALTH_CODE=<"%TEMP%\health_code.txt"

if "%HEALTH_CODE%"=="200" (
    echo [OK] Backend health check passed (HTTP 200)
) else (
    echo [ERROR] Backend health check failed (HTTP %HEALTH_CODE%)
    docker compose logs backend
    docker compose down
    exit /b 1
)

REM Test frontend
echo.
echo --- Testing frontend ---
curl -s -o nul -w "%%{http_code}" http://localhost:4000/ > "%TEMP%\frontend_code.txt"
set /p FRONTEND_CODE=<"%TEMP%\frontend_code.txt"

if "%FRONTEND_CODE%"=="200" (
    echo [OK] Frontend accessible (HTTP 200)
) else (
    echo [ERROR] Frontend not accessible (HTTP %FRONTEND_CODE%)
    docker compose logs frontend
    docker compose down
    exit /b 1
)

REM Cleanup
echo.
echo --- Cleaning up ---
docker compose down

echo.
echo ============================================
echo   ALL TESTS PASSED
echo ============================================
echo.
echo Containers tested successfully:
echo   - Backend: http://localhost:4001
echo   - Frontend: http://localhost:4000
echo.

exit /b 0
