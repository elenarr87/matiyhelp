<#
Convert images in ./images to WebP and AVIF using ImageMagick (magick).
Creates ./images/webp and ./images/avif and does NOT overwrite originals.
Excludes files whose names contain 'logo' or 'favicon'.

Usage: run from repository root in PowerShell:
  pwsh .\scripts\convert_images.ps1

Requires ImageMagick installed and `magick` available in PATH.
#>

Write-Host "Starting image conversion..." -ForegroundColor Cyan

$imagesPath = Join-Path (Get-Location) 'images'
if (-not (Test-Path $imagesPath)) {
    Write-Error "Images folder not found: $imagesPath"
    exit 1
}

$webpDir = Join-Path $imagesPath 'webp'
$avifDir = Join-Path $imagesPath 'avif'

New-Item -ItemType Directory -Path $webpDir -Force | Out-Null
New-Item -ItemType Directory -Path $avifDir -Force | Out-Null

$magick = Get-Command magick -ErrorAction SilentlyContinue
if (-not $magick) {
    Write-Error "ImageMagick 'magick' not found in PATH. Install ImageMagick or ensure 'magick' is available."
    exit 1
}

$files = Get-ChildItem -Path $imagesPath -Include *.jpg,*.jpeg,*.png -File -Recurse |
    Where-Object { $_.FullName -notmatch '\\images\\webp' -and $_.FullName -notmatch '\\images\\avif' }

foreach ($f in $files) {
    $name = $f.Name.ToLower()
    if ($name -match 'logo' -or $name -match 'favicon') {
        Write-Host "Skipping (logo/favicon): $($f.FullName)" -ForegroundColor Yellow
        continue
    }

    $base = $f.BaseName
    $webpOut = Join-Path $webpDir ($base + '.webp')
    $avifOut = Join-Path $avifDir ($base + '.avif')

    try {
        Write-Host "Converting to WebP: $($f.FullName) -> $webpOut"
        & magick $f.FullName -quality 80 $webpOut
    } catch {
        Write-Warning "WebP conversion failed for $($f.FullName): $_"
    }

    try {
        Write-Host "Converting to AVIF: $($f.FullName) -> $avifOut"
        & magick $f.FullName -quality 50 $avifOut
    } catch {
        Write-Warning "AVIF conversion failed for $($f.FullName): $_"
    }
}

Write-Host "Image conversion finished. Converted files are in $webpDir and $avifDir" -ForegroundColor Green
