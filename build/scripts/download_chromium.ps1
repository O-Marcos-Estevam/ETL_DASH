# ============================================================
# Download Chromium Portable
# ============================================================

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = $PSScriptRoot
$BUILD_DIR = Split-Path $SCRIPT_DIR -Parent
$ROOT = Split-Path $BUILD_DIR -Parent
$OUTPUT = "$ROOT\dist\ETL_Dashboard\runtime"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       Download Chromium Portable" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Criar diretórios
New-Item -ItemType Directory -Force -Path "$OUTPUT\chromium" | Out-Null
New-Item -ItemType Directory -Force -Path "$OUTPUT\drivers" | Out-Null

# URLs (Chromium for Testing - versão estável)
$CHROME_VERSION = "121.0.6167.85"
$CHROME_URL = "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/win64/chrome-win64.zip"
$DRIVER_URL = "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/win64/chromedriver-win64.zip"

$TEMP_DIR = "$env:TEMP\etl_chrome_download"
New-Item -ItemType Directory -Force -Path $TEMP_DIR | Out-Null

# Download Chrome
Write-Host "[1/4] Baixando Chrome for Testing..." -ForegroundColor Yellow
$chromeZip = "$TEMP_DIR\chrome.zip"
Invoke-WebRequest -Uri $CHROME_URL -OutFile $chromeZip -UseBasicParsing

# Extrair Chrome
Write-Host "[2/4] Extraindo Chrome..." -ForegroundColor Yellow
Expand-Archive -Path $chromeZip -DestinationPath $TEMP_DIR -Force
Copy-Item "$TEMP_DIR\chrome-win64\*" "$OUTPUT\chromium\" -Recurse -Force

# Download ChromeDriver
Write-Host "[3/4] Baixando ChromeDriver..." -ForegroundColor Yellow
$driverZip = "$TEMP_DIR\chromedriver.zip"
Invoke-WebRequest -Uri $DRIVER_URL -OutFile $driverZip -UseBasicParsing

# Extrair ChromeDriver
Write-Host "[4/4] Extraindo ChromeDriver..." -ForegroundColor Yellow
Expand-Archive -Path $driverZip -DestinationPath $TEMP_DIR -Force
Copy-Item "$TEMP_DIR\chromedriver-win64\chromedriver.exe" "$OUTPUT\drivers\" -Force

# Limpar
Remove-Item -Recurse -Force $TEMP_DIR -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "       Download Concluído!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Chrome: $OUTPUT\chromium\chrome.exe"
Write-Host "Driver: $OUTPUT\drivers\chromedriver.exe"
Write-Host ""
