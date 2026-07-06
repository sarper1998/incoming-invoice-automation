param(
  [string]$WebDir = "web"
)

$ErrorActionPreference = "Stop"

$source = Resolve-Path -LiteralPath $WebDir
$buildRoot = Join-Path $env:TEMP ("incoming-invoice-ui-build-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
$pushed = $false

try {
  Copy-Item -LiteralPath (Join-Path $source "package.json") -Destination $buildRoot
  Copy-Item -LiteralPath (Join-Path $source "index.html") -Destination $buildRoot
  Copy-Item -LiteralPath (Join-Path $source "vite.config.js") -Destination $buildRoot
  Copy-Item -LiteralPath (Join-Path $source "src") -Destination $buildRoot -Recurse

  Push-Location $buildRoot
  $pushed = $true
  npm install --no-audit --no-fund --loglevel=warn
  npm run build
  Pop-Location
  $pushed = $false

  $distTarget = Join-Path $source "dist"
  if (Test-Path $distTarget) {
    Remove-Item -LiteralPath $distTarget -Recurse -Force
  }
  Copy-Item -LiteralPath (Join-Path $buildRoot "dist") -Destination $distTarget -Recurse
  Get-ChildItem -LiteralPath $distTarget -Recurse -File |
    Select-Object FullName, Length
}
finally {
  if ($pushed) {
    Pop-Location -ErrorAction SilentlyContinue
  }
  if (Test-Path $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
  }
}
