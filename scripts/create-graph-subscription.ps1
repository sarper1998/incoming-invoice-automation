param(
  [Parameter(Mandatory = $true)] [string]$NotificationUrl,
  [Parameter(Mandatory = $true)] [string]$GraphTenantId,
  [Parameter(Mandatory = $true)] [string]$GraphClientId,
  [Parameter(Mandatory = $true)] [string]$GraphClientSecret,
  [Parameter(Mandatory = $true)] [string]$GraphMailbox,
  [string]$WorkerSharedSecretPath = ".worker-secret.local.txt"
)

$ErrorActionPreference = "Stop"

$env:GRAPH_TENANT_ID = $GraphTenantId
$env:GRAPH_CLIENT_ID = $GraphClientId
$env:GRAPH_CLIENT_SECRET = $GraphClientSecret
$env:GRAPH_MAILBOX = $GraphMailbox
$env:WORKER_SHARED_SECRET = (Get-Content -LiteralPath $WorkerSharedSecretPath -Raw).Trim()

uv run python -m invoice_automation.cli subscribe --notification-url $NotificationUrl
