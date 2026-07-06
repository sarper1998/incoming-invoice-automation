# Incoming Invoice Automation

This is the first safe slice of the architecture: extract structured invoice data from PDF e-invoices before connecting Microsoft Graph or SAP APIs.

For private Turkish e-invoice PDF samples, the parser uses:

- embedded XML detection first
- QR payload extraction for official invoice header and totals
- PDF table/text extraction for line descriptions and cross-checks
- QR-vs-PDF validation before producing canonical JSON

## Run

```powershell
uv run --extra test python -m invoice_automation.cli extract "sample-invoice.pdf" --output output/sample-invoice.json
```

Without an output file, JSON is written to stdout:

```powershell
uv run python -m invoice_automation.cli extract "sample-invoice.pdf"
```

CSV summary:

```powershell
uv run python -m invoice_automation.cli extract "sample-invoice.pdf" --format csv --output output/sample-invoice.csv
```

## Test

```powershell
uv run --extra test pytest
```

Real invoice PDFs are intentionally not committed. If you want to run the private parser smoke tests against a local sample, set:

```powershell
$env:PRIVATE_INVOICE_SAMPLE_PDF = "C:\path\to\sample-invoice.pdf"
uv run --extra test pytest tests\test_sever_yacht_parser.py
```

## Mail Worker

The BTP app exposes:

- `GET /health`
- `GET /` for the React admin UI
- `POST /api/extract` for multipart PDF extraction tests
- `GET/PUT /api/settings` for runtime mailbox, Graph, poller, and SAP posting-user settings
- `GET/DELETE /api/logs?type=mail_read|sap_record` for read-mail and SAP-record activity logs
- `GET/PUT /api/mapping` for SAP payload mapping
- `POST /jobs/process-mail` for the Microsoft Graph mailbox worker
- `POST /jobs/process-manual` for Manual-folder retry

The mail worker requires `WORKER_SHARED_SECRET` and Microsoft Graph app-only settings. It currently runs with `SAP_MODE=dry-run`, so it extracts and validates invoices but does not post to SAP.

The React admin UI can now maintain:

- English/Turkish UI language selection
- which mailbox and folder will be read
- Microsoft Graph app-only credentials
- poller interval and enabled/disabled state
- SAP mode, target placeholders, and the posting user label
- separate logs for `mail_read` and `sap_record`

By default these runtime settings and logs are stored under `data/`. This keeps the first slice cheap and dependency-free, but Cloud Foundry instance disk is not a durable production store across restage/redeploy. Move `APP_SETTINGS_PATH` and `APP_LOG_PATH` to a bound durable service if these records must survive runtime replacement.

When SAP mapping is incomplete, the worker returns `manual` and moves the mail to the `Manual` folder instead of creating a wrong invoice. The mapping must resolve at least:

- seller tax ID to SAP supplier/BP number
- buyer tax ID to company code
- VAT rate to SAP tax code
- supplier or default GL account

After a user corrects the mapping, trigger Manual-folder retry:

```powershell
.\scripts\invoke-mail-job.ps1 `
  -Route "https://<app-route>" `
  -WorkerSharedSecret "<secret>" `
  -Path "/jobs/process-manual"
```

Mapping can be provided through `SAP_MAPPING_JSON` or `SAP_MAPPING_PATH`; see `config/sap_mapping.example.json`.

For no-cost event triggering, create a Microsoft Graph webhook subscription that posts new-message notifications to:

```text
https://<app-route>/graph/notifications
```

The endpoint validates Microsoft Graph subscription handshakes and then checks `clientState` before processing notifications.

To avoid SAP BTP Job Scheduler cost completely, the app can also run its own lightweight mailbox poller:

```text
MAIL_POLLER_ENABLED=true
MAIL_POLL_INTERVAL_SECONDS=300
```

With one CF instance this checks the source folder every 5 minutes. Processed messages are moved out of the source folder, so the next run does not pick them up again.

Implementation support documents:

- [Customer questionnaire](docs/CUSTOMER_QUESTIONNAIRE.md)
- [LinkedIn article draft](docs/LINKEDIN_ARTICLE_EN.md)

Current code implements the Microsoft Graph mailbox connector. Google Workspace/Gmail is documented as an equivalent extension scenario; it needs a Gmail API connector before runtime use.

## BTP Deploy

Build:

```powershell
.\scripts\build-ui.ps1
mbt build -p cf
```

Deploy after `cf login` is valid:

```powershell
cf deploy mta_archives\incoming-invoice-automation_0.1.0.mtar
```

Set environment variables and restage:

```powershell
.\scripts\set-cf-env.ps1 `
  -WorkerSharedSecret "<secret>" `
  -GraphTenantId "<tenant-id>" `
  -GraphClientId "<client-id>" `
  -GraphClientSecret "<client-secret>" `
  -GraphMailbox "<mailbox@domain.com>"
```

Trigger one mailbox run:

```powershell
.\scripts\invoke-mail-job.ps1 `
  -Route "https://<app-route>" `
  -WorkerSharedSecret "<secret>"
```

Create the Graph webhook subscription after the Graph env vars are available locally:

```powershell
$env:WORKER_SHARED_SECRET = Get-Content .worker-secret.local.txt -Raw
uv run python -m invoice_automation.cli subscribe `
  --notification-url "https://<app-route>/graph/notifications"
```

## Next SAP Slice

After the extraction contract is accepted:

1. Microsoft Graph reads one scoped mailbox and downloads PDF attachments.
2. This parser produces canonical invoice JSON.
3. Business rule mapping fills SAP-only fields such as supplier ID, GL account, cost center, and tax code.
4. SAP S/4HANA Public Cloud supplier invoice API is called.
5. The mail is moved to `Processed`, `Manual`, or `Error`.
