@echo off
echo ============================================================
echo   ETL Dashboard V2 - Build
echo ============================================================
echo.

cd /d "%~dp0.."

echo [1/3] Compilando Backend Java...
cd backend
call mvn clean package -DskipTests
if %errorlevel% neq 0 (
    echo ERRO: Falha ao compilar backend
    pause
    exit /b 1
)

echo.
echo [2/3] Instalando dependencias Frontend...
cd ..\frontend
call npm install
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar dependencias
    pause
    exit /b 1
)

echo.
echo [3/3] Compilando Frontend TypeScript...
call npm run build
if %errorlevel% neq 0 (
    echo ERRO: Falha ao compilar frontend
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Build concluido com sucesso!
echo ============================================================
echo.
echo Backend: backend\target\etl-dashboard-2.0.0.jar
echo Frontend: frontend\dist\
echo.
pause
