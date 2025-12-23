@echo off
chcp 65001 >nul
title ETL Dashboard V2
color 0A

:: Define diretorio raiz e navega para ele
pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd
cd /d "%ROOT_DIR%"

echo.
echo  ============================================================
echo    ETL Dashboard V2
echo  ============================================================
echo    Raiz: %CD%
echo.

set "JAVA_HOME=%ROOT_DIR%\java\jdk-17.0.2"
set "MAVEN_HOME=%ROOT_DIR%\maven\apache-maven-3.9.6"
set "NODE_HOME=%ROOT_DIR%\node"
set "PATH=%JAVA_HOME%\bin;%MAVEN_HOME%\bin;%NODE_HOME%;%PATH%"

echo [0/5] Checando processos...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4000 :4001" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo       Limpeza OK

echo [1/5] Checando Java...
"%JAVA_HOME%\bin\java.exe" -version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Java nao encontrado. Verifique a pasta 'java'.
    pause
    exit /b 1
)

echo [2/5] Checando Node...
"%NODE_HOME%\node.exe" -v >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node nao encontrado em: %NODE_HOME%
    pause
    exit /b 1
)
echo       OK ('%NODE_HOME%')

echo [3/5] Checando Maven...
call "%MAVEN_HOME%\bin\mvn.cmd" -v >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Maven nao encontrado. Verifique a pasta 'maven'.
    pause
    exit /b 1
)

echo [4/5] Atualizando Backend...
cd backend
call "%MAVEN_HOME%\bin\mvn.cmd" clean package -DskipTests -q
if errorlevel 1 (
    echo [ERRO] Falha ao compilar o backend.
    pause
    exit /b 1
)
cd ..
echo       Compilacao OK

echo [5/5] Iniciando janelas...

echo  - Iniciando Backend (Porta 4001)...
:: Usa caminho relativo simples
start "ETL-Backend" cmd /c "scripts\start-backend.bat"

echo    Aguardando 10s...
timeout /t 10

echo  - Iniciando Frontend (Porta 4000)...
start "ETL-Frontend" cmd /c "scripts\start-frontend.bat"

echo    Aguardando 5s...
timeout /t 5

echo.
echo  - Abrindo navegador (http://localhost:4000)...
start "" "http://localhost:4000"
if errorlevel 1 (
    echo    'start' falhou, tentando 'explorer'...
    explorer "http://localhost:4000"
)

echo.
echo  ============================================================
echo    SISTEMA INICIADO
echo  ============================================================
echo.
echo  Se as janelas 'ETL-Backend' e 'ETL-Frontend' abriram e fecharam,
echo  houve um erro na execucao delas.
echo.
echo  Pressione qualquer tecla para sair...
pause >nul
