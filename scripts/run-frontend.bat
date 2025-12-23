@echo off
echo ============================================================
echo   ETL Dashboard V2 - Frontend TypeScript
echo ============================================================
echo.

cd /d "%~dp0..\frontend"

echo Porta: 4000
echo.

:: Verifica se node_modules existe
if not exist "node_modules" (
    echo Instalando dependencias...
    npm install
    if errorlevel 1 (
        echo [ERRO] Falha na instalacao!
        pause
        exit /b 1
    )
)

echo Iniciando servidor de desenvolvimento...
npm run dev

pause
