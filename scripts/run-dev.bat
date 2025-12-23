@echo off
echo ============================================================
echo   ETL Dashboard V2 - Modo Desenvolvimento
echo ============================================================
echo.

cd /d "%~dp0.."

echo Iniciando Backend e Frontend em paralelo...
echo.

start "ETL Backend" cmd /k "cd backend && mvn spring-boot:run"
timeout /t 10 /nobreak >nul
start "ETL Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://localhost:4001
echo Frontend: http://localhost:4000
echo.
echo Aguarde o backend iniciar completamente...
echo Pressione qualquer tecla para abrir o navegador...
pause >nul

start http://localhost:4000

