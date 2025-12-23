param([string]$Source, [string]$Destination)

Add-Type -AssemblyName System.Drawing

if (-not (Test-Path $Source)) {
    Write-Error "Imagem nao encontrada: $Source"
    exit 1
}

Write-Host "Carregando imagem..."
$srcImage = [System.Drawing.Image]::FromFile($Source)

# Tamanho padrao de icone grande no Windows
$size = 64
# Nota: 256 pode ser grande para alguns caches, 64 é seguro e bonito.

Write-Host "Redimensionando para ${size}x${size}..."
$newBmp = New-Object System.Drawing.Bitmap($size, $size)
$g = [System.Drawing.Graphics]::FromImage($newBmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$g.Clear([System.Drawing.Color]::Transparent)

# Logica de Crop (Preencher quadrado)
$ratio = [Math]::Max($size / $srcImage.Width, $size / $srcImage.Height)
$w = [int]($srcImage.Width * $ratio)
$h = [int]($srcImage.Height * $ratio)
$x = [int](($size - $w) / 2)
$y = [int](($size - $h) / 2)

$g.DrawImage($srcImage, $x, $y, $w, $h)
$g.Dispose()

Write-Host "Convertendo e Salvando..."
try {
    $iconHandle = $newBmp.GetHicon()
    $icon = [System.Drawing.Icon]::FromHandle($iconHandle)
    
    $fs = New-Object System.IO.FileStream($Destination, "Create")
    $icon.Save($fs)
    $fs.Close()
    
    $icon.Dispose()
    Write-Host "Sucesso! Icone salvo em: $Destination"
} catch {
    Write-Error "Erro ao salvar icone: $_"
}

$newBmp.Dispose()
$srcImage.Dispose()
