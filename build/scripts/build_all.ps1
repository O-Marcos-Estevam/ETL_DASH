# ============================================================
# ETL Dashboard - Build Completo
# ============================================================
# Gera o executável standalone do ETL Dashboard
# ============================================================

param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

# Diretórios
$SCRIPT_DIR = $PSScriptRoot
$BUILD_DIR = Split-Path $SCRIPT_DIR -Parent
$ROOT = Split-Path $BUILD_DIR -Parent
$DIST = "$ROOT\dist\ETL_Dashboard"
$PYINSTALLER_DIR = "$BUILD_DIR\pyinstaller"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       ETL Dashboard - Build Completo" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Root: $ROOT" -ForegroundColor Gray
Write-Host "Output: $DIST" -ForegroundColor Gray
Write-Host ""

# Limpar se solicitado
if ($Clean) {
    Write-Host "[1/5] Limpando builds anteriores..." -ForegroundColor Yellow
    if (Test-Path $DIST) {
        Remove-Item -Recurse -Force $DIST
    }
    if (Test-Path "$PYINSTALLER_DIR\dist") {
        Remove-Item -Recurse -Force "$PYINSTALLER_DIR\dist"
    }
    if (Test-Path "$PYINSTALLER_DIR\build") {
        Remove-Item -Recurse -Force "$PYINSTALLER_DIR\build"
    }
}

# 1. Build Frontend
if (-not $SkipFrontend) {
    Write-Host "[2/5] Building Frontend..." -ForegroundColor Yellow
    
    Push-Location "$ROOT\frontend"
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "Falha no build do frontend"
        }
    } finally {
        Pop-Location
    }
    
    Write-Host "      Frontend build concluído!" -ForegroundColor Green
} else {
    Write-Host "[2/5] Frontend: SKIP" -ForegroundColor Gray
}

# 2. Build Backend
if (-not $SkipBackend) {
    Write-Host "[3/5] Building Backend (PyInstaller)..." -ForegroundColor Yellow
    
    Push-Location $PYINSTALLER_DIR
    try {
        pyinstaller backend.spec --noconfirm
        if ($LASTEXITCODE -ne 0) {
            throw "Falha no build do backend"
        }
    } finally {
        Pop-Location
    }
    
    Write-Host "      Backend build concluído!" -ForegroundColor Green
}

# 3. Build Launcher
Write-Host "[4/5] Building Launcher..." -ForegroundColor Yellow

Push-Location $PYINSTALLER_DIR
try {
    pyinstaller launcher.spec --noconfirm
    if ($LASTEXITCODE -ne 0) {
        throw "Falha no build do launcher"
    }
} finally {
    Pop-Location
}

Write-Host "      Launcher build concluído!" -ForegroundColor Green

# 4. Montar distribuição
Write-Host "[5/5] Montando distribuição..." -ForegroundColor Yellow

# Criar estrutura
New-Item -ItemType Directory -Force -Path $DIST | Out-Null
New-Item -ItemType Directory -Force -Path "$DIST\runtime\backend" | Out-Null
New-Item -ItemType Directory -Force -Path "$DIST\runtime\chromium" | Out-Null
New-Item -ItemType Directory -Force -Path "$DIST\runtime\drivers" | Out-Null
New-Item -ItemType Directory -Force -Path "$DIST\config" | Out-Null
New-Item -ItemType Directory -Force -Path "$DIST\data" | Out-Null
New-Item -ItemType Directory -Force -Path "$DIST\logs" | Out-Null
New-Item -ItemType Directory -Force -Path "$DIST\web" | Out-Null

# Copiar launcher
Copy-Item "$PYINSTALLER_DIR\dist\ETL_Dashboard.exe" "$DIST\" -Force

# Copiar backend
Copy-Item "$PYINSTALLER_DIR\dist\backend\*" "$DIST\runtime\backend\" -Recurse -Force

# Copiar frontend
if (Test-Path "$ROOT\frontend\dist") {
    Copy-Item "$ROOT\frontend\dist\*" "$DIST\web\" -Recurse -Force
}

# Copiar config (exemplo)
if (Test-Path "$ROOT\config\credentials.example.json") {
    Copy-Item "$ROOT\config\credentials.example.json" "$DIST\config\credentials.json" -Force
}

# Criar README
@"
ETL Dashboard v2.1.0
====================

Para iniciar:
1. Execute ETL_Dashboard.exe
2. O navegador abrirá automaticamente
3. Configure as credenciais em Settings

Requisitos:
- Windows 10/11 x64
- Google Chrome instalado (ou coloque Chromium portátil em runtime/chromium/)

Suporte:
- Verifique logs em logs/
- Documentação em docs/
"@ | Out-File -FilePath "$DIST\README.txt" -Encoding utf8

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "       Build Concluído com Sucesso!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output: $DIST" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Yellow
Write-Host "  1. Copie Chromium portátil para $DIST\runtime\chromium\"
Write-Host "  2. Teste executando $DIST\ETL_Dashboard.exe"
Write-Host "  3. Gere o instalador com Inno Setup"
Write-Host ""
