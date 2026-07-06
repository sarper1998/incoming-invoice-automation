param(
  [string]$MtarPath = "mta_archives\incoming-invoice-automation_0.1.0.mtar"
)

$ErrorActionPreference = "Stop"

cf target
mbt build -p cf
$deployLog = Join-Path $env:TEMP ("incoming-invoice-cf-deploy-" + [guid]::NewGuid().ToString() + ".log")
cf deploy $MtarPath *> $deployLog
$deployCode = $LASTEXITCODE
Get-Content -LiteralPath $deployLog |
  Select-String -Pattern 'Operation ID|Process finished|started and available|FAILED|WARNING|Uploading 1 files|Detected MTA|Detected deployed MTA|Detected new MTA|Updating application|Stopping application|Staging application|Starting application|Skipping deletion|Authentication'
Remove-Item -LiteralPath $deployLog -Force -ErrorAction SilentlyContinue
if ($deployCode -ne 0) {
  exit $deployCode
}
cf app incoming-invoice-automation-srv
