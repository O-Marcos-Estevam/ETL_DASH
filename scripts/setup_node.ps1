$Url = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-win-x64.zip"
$ZipFile = "$PSScriptRoot\node.zip"
$ExtractPath = "$PSScriptRoot\node_temp"
$DestPath = "$PSScriptRoot\..\node"

Write-Host "=== Instalando Node.js Portable ==="
Write-Host "URL: $Url"

Write-Host "1/4 Baixando..."
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $Url -OutFile $ZipFile

Write-Host "2/4 Extraindo..."
Expand-Archive -Path $ZipFile -DestinationPath $ExtractPath -Force

Write-Host "3/4 Configurando..."
if (Test-Path $DestPath) { Remove-Item -Recurse -Force $DestPath }
$SubFolder = Get-ChildItem -Path $ExtractPath | Select-Object -First 1
Move-Item -Path $SubFolder.FullName -Destination $DestPath

Write-Host "4/4 Limpando temporarios..."
Remove-Item -Force $ZipFile
Remove-Item -Recurse -Force $ExtractPath

Write-Host "SUCESSO: Node.js instalado em $DestPath"
Start-Sleep -Seconds 3
