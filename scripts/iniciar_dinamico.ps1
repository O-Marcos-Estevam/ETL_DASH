# Script de Inicializacao Dinamica de Portas

function Test-PortAvailable {
    param($Port)
    $con = (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue)
    return ($con -eq $null)
}

function Get-FreePort {
    param($StartPort)
    $port = $StartPort
    while (-not (Test-PortAvailable $port)) {
        Write-Host "Porta $port ocupada, tentando proxima..." -ForegroundColor Yellow
        $port++
        if ($port -gt 65000) { throw "Nenhuma porta livre encontrada!" }
    }
    return $port
}

Clear-Host
Write-Host "=== ETL Dashboard V2: Modo Dinamico ===" -ForegroundColor Cyan

# 1. Backend
Write-Host "Buscando porta Backend (4001+)..."
$BackendPort = Get-FreePort 4001
Write-Host "-> Backend: $BackendPort" -ForegroundColor Green

# 2. Frontend
Write-Host "Buscando porta Frontend (4000+)..."
$FrontendPort = Get-FreePort 4000
while ($FrontendPort -eq $BackendPort -or -not (Test-PortAvailable $FrontendPort)) {
    $FrontendPort++
}
Write-Host "-> Frontend: $FrontendPort" -ForegroundColor Green

# 3. Variaveis
$env:ETL_BACKEND_PORT = $BackendPort
$env:PORT = $FrontendPort
$env:BACKEND_PORT = $BackendPort

# 4. Iniciar
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$Root = Resolve-Path "$ScriptDir\.."

Write-Host "Iniciando Backend..."
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$Root\scripts\start-backend.bat`"" -WorkingDirectory "$Root"
Start-Sleep -Seconds 15

Write-Host "Iniciando Frontend..."
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$Root\scripts\start-frontend.bat`"" -WorkingDirectory "$Root"
Start-Sleep -Seconds 5

$URL = "http://localhost:$FrontendPort"
Write-Host "Abrindo: $URL"
Start-Process $URL

Read-Host "Pressione Enter para sair..."
