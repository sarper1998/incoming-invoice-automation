param(
  [Parameter(Mandatory = $true)] [string]$Route,
  [Parameter(Mandatory = $true)] [string]$WorkerSharedSecret,
  [string]$Path = "/jobs/process-mail"
)

$ErrorActionPreference = "Stop"

$uri = $Route.TrimEnd("/") + "/" + $Path.TrimStart("/")
Invoke-RestMethod `
  -Method Post `
  -Uri $uri `
  -Headers @{ Authorization = "Bearer $WorkerSharedSecret" }
