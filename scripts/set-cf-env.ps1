param(
  [Parameter(Mandatory = $true)] [string]$WorkerSharedSecret,
  [Parameter(Mandatory = $true)] [string]$GraphTenantId,
  [Parameter(Mandatory = $true)] [string]$GraphClientId,
  [Parameter(Mandatory = $true)] [string]$GraphClientSecret,
  [Parameter(Mandatory = $true)] [string]$GraphMailbox,
  [string]$SourceFolder = "Inbox",
  [string]$ProcessedFolder = "Processed",
  [string]$ManualFolder = "Manual",
  [string]$ErrorFolder = "Error",
  [string]$SubjectKeywords = "e-Fatura,e-Arşiv,Fatura",
  [string]$SapMode = "dry-run",
  [string]$SapPostingUser = "",
  [string]$AppName = "incoming-invoice-automation-srv"
)

$ErrorActionPreference = "Stop"

cf set-env $AppName WORKER_SHARED_SECRET $WorkerSharedSecret
cf set-env $AppName GRAPH_TENANT_ID $GraphTenantId
cf set-env $AppName GRAPH_CLIENT_ID $GraphClientId
cf set-env $AppName GRAPH_CLIENT_SECRET $GraphClientSecret
cf set-env $AppName GRAPH_MAILBOX $GraphMailbox
cf set-env $AppName GRAPH_SOURCE_FOLDER $SourceFolder
cf set-env $AppName GRAPH_PROCESSED_FOLDER $ProcessedFolder
cf set-env $AppName GRAPH_MANUAL_FOLDER $ManualFolder
cf set-env $AppName GRAPH_ERROR_FOLDER $ErrorFolder
cf set-env $AppName GRAPH_SUBJECT_KEYWORDS $SubjectKeywords
cf set-env $AppName SAP_MODE $SapMode
if ($SapPostingUser) {
  cf set-env $AppName SAP_POSTING_USER $SapPostingUser
}
cf restage $AppName
