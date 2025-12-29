# Script de Teste Minucioso do Backend ETL
$baseUrl = "http://localhost:4002/api"
$results = @()

function Test-Endpoint {
    param (
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [string]$Description
    )
    
    Write-Host "`n=== $Description ===" -ForegroundColor Cyan
    Write-Host "$Method $Endpoint" -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = "$baseUrl$Endpoint"
            Method = $Method
            ContentType = "application/json"
            UseBasicParsing = $true
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-WebRequest @params
        $content = $response.Content | ConvertFrom-Json
        
        $status = "✅ PASSOU"
        $color = "Green"
        
        Write-Host "Status: $($response.StatusCode)" -ForegroundColor $color
        if ($content | Get-Member -Name "sistemas" -MemberType NoteProperty) {
            Write-Host "Sistemas encontrados: $($content.sistemas.PSObject.Properties.Count)"
        }
        if ($content | Get-Member -Name "status" -MemberType NoteProperty) {
            Write-Host "Status: $($content.status)"
        }
        
        $results += [PSCustomObject]@{
            Endpoint = "$Method $Endpoint"
            Status = "✅ PASSOU"
            StatusCode = $response.StatusCode
            Description = $Description
        }
        
        return $content
    }
    catch {
        $status = "❌ FALHOU"
        $color = "Red"
        
        Write-Host "Status: $status" -ForegroundColor $color
        Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Host "StatusCode: $statusCode" -ForegroundColor Red
        }
        
        $results += [PSCustomObject]@{
            Endpoint = "$Method $Endpoint"
            Status = "❌ FALHOU"
            StatusCode = $statusCode
            Description = $Description
            Error = $_.Exception.Message
        }
        
        return $null
    }
}

Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "TESTE MINUCIOSO DO BACKEND ETL" -ForegroundColor Magenta
Write-Host "========================================`n" -ForegroundColor Magenta

# 1. Health Check
Test-Endpoint -Method "GET" -Endpoint "/health" -Description "Health Check"

# 2. Obter Configuração
$config = Test-Endpoint -Method "GET" -Endpoint "/config" -Description "Obter Configuração Completa"

# 3. Obter Sistemas
$sistemas = Test-Endpoint -Method "GET" -Endpoint "/sistemas" -Description "Listar Todos os Sistemas"

# 4. Obter Sistemas Ativos
Test-Endpoint -Method "GET" -Endpoint "/sistemas/ativos" -Description "Listar Sistemas Ativos"

# 5. Obter Sistema Específico (se houver sistemas)
if ($sistemas -and $sistemas.PSObject.Properties.Count -gt 0) {
    $primeiroSistema = ($sistemas.PSObject.Properties | Select-Object -First 1).Name
    Test-Endpoint -Method "GET" -Endpoint "/sistemas/$primeiroSistema" -Description "Obter Sistema Específico ($primeiroSistema)"
}

# 6. Obter Credenciais (mascaradas)
$credenciais = Test-Endpoint -Method "GET" -Endpoint "/credentials" -Description "Obter Credenciais (Mascaradas)"

# 7. Obter Paths
Test-Endpoint -Method "GET" -Endpoint "/config/paths" -Description "Obter Caminhos Configurados"

# 8. Listar Jobs
Test-Endpoint -Method "GET" -Endpoint "/jobs" -Description "Listar Jobs de Execução"

# 9. Teste de Execução (dry-run)
if ($sistemas -and $sistemas.PSObject.Properties.Count -gt 0) {
    $primeiroSistema = ($sistemas.PSObject.Properties | Select-Object -First 1).Name
    $dataHoje = (Get-Date).ToString("yyyy-MM-dd")
    
    $executeBody = @{
        sistemas = @($primeiroSistema)
        dry_run = $true
        data_inicial = $dataHoje
        data_final = $dataHoje
    }
    
    $executeResult = Test-Endpoint -Method "POST" -Endpoint "/execute" -Body $executeBody -Description "Teste de Execução (Dry-Run)"
}

# Resumo
Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "RESUMO DOS TESTES" -ForegroundColor Magenta
Write-Host "========================================`n" -ForegroundColor Magenta

$results | Format-Table -AutoSize

$passou = ($results | Where-Object { $_.Status -eq "✅ PASSOU" }).Count
$falhou = ($results | Where-Object { $_.Status -eq "❌ FALHOU" }).Count
$total = $results.Count

Write-Host "`nTotal: $total" -ForegroundColor White
Write-Host "Passou: $passou" -ForegroundColor Green
Write-Host "Falhou: $falhou" -ForegroundColor $(if ($falhou -gt 0) { "Red" } else { "Green" })

if ($falhou -eq 0) {
    Write-Host "`n✅ TODOS OS TESTES PASSARAM!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Alguns testes falharam. Verifique os erros acima." -ForegroundColor Yellow
}


