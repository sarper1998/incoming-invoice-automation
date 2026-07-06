from __future__ import annotations

from typing import Any

from .mapping import SapMapping


class SapInvoiceClient:
    def __init__(
        self,
        mode: str = "dry-run",
        mapping: SapMapping | None = None,
        posting_user: str | None = None,
    ):
        self.mode = mode
        self.mapping = mapping or SapMapping.from_env()
        self.posting_user = posting_user

    def create_supplier_invoice(self, invoice: dict[str, Any]) -> dict[str, Any]:
        resolution = self.mapping.resolve(invoice)
        if not resolution.complete:
            return {
                "status": "manual",
                "mode": self.mode,
                "posted": False,
                "invoiceNo": invoice.get("invoiceNo"),
                "ettn": invoice.get("ettn"),
                "sellerTaxId": invoice.get("sellerTaxId"),
                "sellerName": invoice.get("sellerName"),
                "postingUser": self.posting_user,
                "missingMappings": resolution.missing,
                "suggestedMapping": resolution.suggested_mapping,
                "reason": "SAP payload mapping is incomplete.",
            }

        if self.mode == "dry-run":
            return {
                "status": "processed",
                "mode": "dry-run",
                "posted": False,
                "invoiceNo": invoice.get("invoiceNo"),
                "ettn": invoice.get("ettn"),
                "postingUser": self.posting_user,
                "resolvedMapping": resolution.values,
                "reason": "SAP posting is disabled; payload mapping resolved.",
            }
        raise NotImplementedError(
            "SAP create is not implemented yet. Approve the payload mapping first."
        )
