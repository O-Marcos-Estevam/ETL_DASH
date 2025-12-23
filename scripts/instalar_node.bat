@echo off
cd /d "%~dp0"
echo Instalando Node.js Portable...
powershell -NoProfile -ExecutionPolicy Bypass -File "setup_node.ps1"
pause
