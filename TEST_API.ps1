# ============================================================================
# ETL Dashboard - Script de Testes Robustos
# Testa todos os endpoints e sistemas ETL
# ============================================================================

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "ETL Dashboard - Testes"

# Configuracao
$BaseUrl = "http://localhost:4001"
$LogFile = Join-Path $PSScriptRoot "logs\test_results.log"

# Contadores
$script:TestsPassed = 0
$script:TestsFailed = 0
$script:TestsSkipped = 0

# ============================================================================
# FUNCOES AUXILIARES
# ============================================================================

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    $logDir = Split-Path $LogFile -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
}

function Write-TestHeader {
    param($Title)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Log "=== $Title ==="
}

function Write-TestResult {
    param($TestName, $Passed, $Details = "")
    
    if ($Passed) {
        Write-Host "  [PASS] " -NoNewline -ForegroundColor Green
        Write-Host $TestName
        $script:TestsPassed++
        Write-Log "PASS: $TestName - $Details"
    } else {
        Write-Host "  [FAIL] " -NoNewline -ForegroundColor Red
        Write-Host "$TestName - $Details"
        $script:TestsFailed++
        Write-Log "FAIL: $TestName - $Details" "ERROR"
    }
}

function Write-SkipResult {
    param($TestName, $Reason)
    Write-Host "  [SKIP] " -NoNewline -ForegroundColor Yellow
    Write-Host "$TestName - $Reason"
    $script:TestsSkipped++
    Write-Log "SKIP: $TestName - $Reason" "WARN"
}

function Invoke-ApiRequest {
    param(
        $Method = "GET",
        $Endpoint,
        $Body = $null
    )
    
    $url = "$BaseUrl$Endpoint"
    $params = @{
        Uri = $url
        Method = $Method
        ContentType = "application/json"
        UseBasicParsing = $true
        TimeoutSec = 30
    }
    
    if ($Body) {
        $params.Body = ($Body | ConvertTo-Json -Depth 10)
    }
    
    try {
        $response = Invoke-WebRequest @params
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Content = $response.Content | ConvertFrom-Json
        }
    } catch {
        return @{
            Success = $false
            StatusCode = $_.Exception.Response.StatusCode.value__
            Error = $_.Exception.Message
        }
    }
}

# ============================================================================
# TESTES
# ============================================================================

function Test-HealthEndpoint {
    Write-TestHeader "1. Health Check"
    
    $result = Invoke-ApiRequest -Endpoint "/api/health"
    
    if ($result.Success -and $result.Content.status -eq "ok") {
        Write-TestResult "GET /api/health" $true "version=$($result.Content.version)"
        return $result.Content.version
    } else {
        Write-TestResult "GET /api/health" $false $result.Error
        return $null
    }
}

function Test-SistemasEndpoint {
    Write-TestHeader "2. Sistemas Endpoints"
    
    # GET /api/sistemas
    $result = Invoke-ApiRequest -Endpoint "/api/sistemas"
    
    if ($result.Success) {
        $sistemas = $result.Content.PSObject.Properties.Name
        Write-TestResult "GET /api/sistemas" $true "Found $($sistemas.Count) sistemas"
        
        # Testar cada sistema individualmente
        foreach ($sistemaId in $sistemas) {
            $singleResult = Invoke-ApiRequest -Endpoint "/api/sistemas/$sistemaId"
            if ($singleResult.Success) {
                $nome = $singleResult.Content.nome
                $ativo = $singleResult.Content.ativo
                $status = $singleResult.Content.status
                Write-TestResult "GET /api/sistemas/$sistemaId" $true "nome='$nome', ativo=$ativo, status=$status"
            } else {
                Write-TestResult "GET /api/sistemas/$sistemaId" $false $singleResult.Error
            }
        }
        
        return $sistemas
    } else {
        Write-TestResult "GET /api/sistemas" $false $result.Error
        return @()
    }
}

function Test-SistemasAtivos {
    Write-TestHeader "3. Sistemas Ativos"
    
    $result = Invoke-ApiRequest -Endpoint "/api/sistemas/ativos"
    
    if ($result.Success) {
        $ativos = $result.Content.PSObject.Properties.Name
        Write-TestResult "GET /api/sistemas/ativos" $true "Found $($ativos.Count) sistemas ativos"
        return $ativos
    } else {
        Write-TestResult "GET /api/sistemas/ativos" $false $result.Error
        return @()
    }
}

function Test-ConfigEndpoint {
    Write-TestHeader "4. Config Endpoint"
    
    $result = Invoke-ApiRequest -Endpoint "/api/config"
    
    if ($result.Success) {
        $version = $result.Content.version
        Write-TestResult "GET /api/config" $true "config version=$version"
        return $result.Content
    } else {
        Write-TestResult "GET /api/config" $false $result.Error
        return $null
    }
}

function Test-JobsEndpoint {
    Write-TestHeader "5. Jobs Endpoint"
    
    # GET /api/jobs
    $result = Invoke-ApiRequest -Endpoint "/api/jobs"
    
    if ($result.Success) {
        $total = $result.Content.total
        Write-TestResult "GET /api/jobs" $true "Found $total jobs in history"
        
        # Testar paginacao
        $resultPaged = Invoke-ApiRequest -Endpoint "/api/jobs?limit=5&offset=0"
        if ($resultPaged.Success) {
            Write-TestResult "GET /api/jobs (paginacao)" $true "limit=5, offset=0"
        } else {
            Write-TestResult "GET /api/jobs (paginacao)" $false $resultPaged.Error
        }
        
        # Testar filtro por status
        foreach ($status in @("completed", "error", "pending", "running", "cancelled")) {
            $resultFiltered = Invoke-ApiRequest -Endpoint "/api/jobs?status=$status"
            if ($resultFiltered.Success) {
                $count = $resultFiltered.Content.total
                Write-TestResult "GET /api/jobs?status=$status" $true "Found $count jobs"
            } else {
                Write-TestResult "GET /api/jobs?status=$status" $false $resultFiltered.Error
            }
        }
        
        # Testar job individual (se existir)
        if ($result.Content.jobs.Count -gt 0) {
            $jobId = $result.Content.jobs[0].id
            $singleJob = Invoke-ApiRequest -Endpoint "/api/jobs/$jobId"
            if ($singleJob.Success) {
                Write-TestResult "GET /api/jobs/$jobId" $true "status=$($singleJob.Content.status)"
            } else {
                Write-TestResult "GET /api/jobs/$jobId" $false $singleJob.Error
            }
        }
        
        return $result.Content.jobs
    } else {
        Write-TestResult "GET /api/jobs" $false $result.Error
        return @()
    }
}

function Test-CredentialsEndpoint {
    Write-TestHeader "6. Credentials Endpoint"
    
    $result = Invoke-ApiRequest -Endpoint "/api/credentials"
    
    if ($result.Success) {
        Write-TestResult "GET /api/credentials" $true "Credentials loaded (masked)"
        return $true
    } else {
        Write-TestResult "GET /api/credentials" $false $result.Error
        return $false
    }
}

function Test-ExecuteDryRun {
    param($Sistemas)
    
    Write-TestHeader "7. Execute Dry Run Test"
    
    if ($Sistemas.Count -eq 0) {
        Write-SkipResult "POST /api/execute (dry_run)" "No sistemas available"
        return
    }
    
    # Pegar primeiro sistema ativo
    $sistemaId = $Sistemas[0]
    
    $body = @{
        sistemas = @($sistemaId)
        dry_run = $true
        limpar = $false
        data_inicial = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
        data_final = (Get-Date).ToString("yyyy-MM-dd")
        opcoes = @{}
    }
    
    $result = Invoke-ApiRequest -Method "POST" -Endpoint "/api/execute" -Body $body
    
    if ($result.Success) {
        if ($result.Content.status -eq "started") {
            Write-TestResult "POST /api/execute (dry_run)" $true "job_id=$($result.Content.job_id)"
            return $result.Content.job_id
        } elseif ($result.Content.status -eq "error" -and $result.Content.message -like "*Ja existe*") {
            Write-SkipResult "POST /api/execute (dry_run)" "Ja existe job em execucao"
            return $null
        } else {
            Write-TestResult "POST /api/execute (dry_run)" $false $result.Content.message
            return $null
        }
    } else {
        Write-TestResult "POST /api/execute (dry_run)" $false $result.Error
        return $null
    }
}

function Test-InvalidRequests {
    Write-TestHeader "8. Invalid Request Handling"
    
    # Sistema inexistente
    $result = Invoke-ApiRequest -Endpoint "/api/sistemas/sistema_inexistente"
    if (-not $result.Success -and $result.StatusCode -eq 404) {
        Write-TestResult "GET /api/sistemas/inexistente (404)" $true "Correctly returned 404"
    } else {
        Write-TestResult "GET /api/sistemas/inexistente (404)" $false "Expected 404"
    }
    
    # Job inexistente
    $result = Invoke-ApiRequest -Endpoint "/api/jobs/99999"
    if (-not $result.Success -and $result.StatusCode -eq 404) {
        Write-TestResult "GET /api/jobs/99999 (404)" $true "Correctly returned 404"
    } else {
        Write-TestResult "GET /api/jobs/99999 (404)" $false "Expected 404"
    }
    
    # Execute sem sistemas
    $body = @{
        sistemas = @()
        dry_run = $true
    }
    $result = Invoke-ApiRequest -Method "POST" -Endpoint "/api/execute" -Body $body
    if (-not $result.Success -and $result.StatusCode -eq 400) {
        Write-TestResult "POST /api/execute (empty sistemas)" $true "Correctly returned 400"
    } elseif ($result.Success -and $result.Content.status -eq "error") {
        Write-TestResult "POST /api/execute (empty sistemas)" $true "Validation working"
    } else {
        Write-TestResult "POST /api/execute (empty sistemas)" $false "Expected validation error"
    }
}

# ============================================================================
# EXECUCAO PRINCIPAL
# ============================================================================

Clear-Host
Write-Host ""
Write-Host ("*" * 60) -ForegroundColor Magenta
Write-Host "*        ETL Dashboard - Suite de Testes Robustos         *" -ForegroundColor Magenta
Write-Host ("*" * 60) -ForegroundColor Magenta
Write-Host ""
Write-Host "Backend URL: $BaseUrl" -ForegroundColor Gray
Write-Host "Log File: $LogFile" -ForegroundColor Gray
Write-Host ""

Write-Log "========== Iniciando Suite de Testes =========="

# Verificar se backend esta rodando
Write-Host "Verificando conexao com o backend..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-WebRequest -Uri "$BaseUrl/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "[OK] Backend esta respondendo!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERRO] Backend nao esta respondendo em $BaseUrl" -ForegroundColor Red
    Write-Host "Certifique-se de que o backend esta rodando antes de executar os testes." -ForegroundColor Red
    Write-Host ""
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Executar testes
$version = Test-HealthEndpoint
$sistemas = Test-SistemasEndpoint
$sistemasAtivos = Test-SistemasAtivos
$config = Test-ConfigEndpoint
$jobs = Test-JobsEndpoint
$credentials = Test-CredentialsEndpoint
$dryRunJobId = Test-ExecuteDryRun -Sistemas $sistemasAtivos
Test-InvalidRequests

# Resumo
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Magenta
Write-Host "                    RESUMO DOS TESTES                      " -ForegroundColor Magenta
Write-Host ("=" * 60) -ForegroundColor Magenta
Write-Host ""
Write-Host "  Testes Passaram:  " -NoNewline
Write-Host $script:TestsPassed -ForegroundColor Green
Write-Host "  Testes Falharam:  " -NoNewline
Write-Host $script:TestsFailed -ForegroundColor $(if ($script:TestsFailed -gt 0) { "Red" } else { "Green" })
Write-Host "  Testes Pulados:   " -NoNewline
Write-Host $script:TestsSkipped -ForegroundColor Yellow
Write-Host ""

$total = $script:TestsPassed + $script:TestsFailed
$percentage = if ($total -gt 0) { [math]::Round(($script:TestsPassed / $total) * 100, 1) } else { 0 }
Write-Host "  Taxa de Sucesso:  $percentage%" -ForegroundColor $(if ($percentage -ge 80) { "Green" } elseif ($percentage -ge 60) { "Yellow" } else { "Red" })
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Magenta

if ($script:TestsFailed -eq 0) {
    Write-Host ""
    Write-Host "  [OK] Todos os testes passaram!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "  [ATENCAO] Alguns testes falharam. Verifique o log: $LogFile" -ForegroundColor Yellow
    Write-Host ""
}

Write-Log "========== Testes Finalizados: $script:TestsPassed passed, $script:TestsFailed failed, $script:TestsSkipped skipped =========="

Write-Host "Pressione Enter para sair..."
Read-Host
