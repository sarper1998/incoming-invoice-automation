from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Any

from .config import WorkerConfig
from .activity_log import append_activity
from .graph_client import GraphClient, MailAttachment, MailMessage
from .pdf_parser import EInvoicePdfParser
from .sap_client import SapInvoiceClient


@dataclass
class AttachmentResult:
    name: str
    status: str
    invoice_count: int = 0
    validation_passed: bool = False
    sap_results: list[dict[str, Any]] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "invoiceCount": self.invoice_count,
            "validationPassed": self.validation_passed,
            "sapResults": self.sap_results or [],
            "error": self.error,
        }


class MailInvoiceWorker:
    def __init__(
        self,
        config: WorkerConfig,
        graph_client: GraphClient | None = None,
        parser: EInvoicePdfParser | None = None,
        sap_client: SapInvoiceClient | None = None,
    ):
        self.config = config
        self.graph = graph_client or GraphClient(config.graph)
        self.parser = parser or EInvoicePdfParser()
        self.sap = sap_client or SapInvoiceClient(
            config.sap_mode,
            posting_user=config.sap_posting_user,
        )

    def run_once(self) -> dict[str, Any]:
        return self.run_folder(self.config.graph.source_folder)

    def run_folder(self, folder_name: str) -> dict[str, Any]:
        messages = self.graph.list_candidate_messages(folder_name)
        processed = []
        for message in messages:
            processed.append(self._process_message(message, current_folder=folder_name))
        return {
            "messageCount": len(messages),
            "processed": processed,
        }

    def process_message_id(self, message_id: str) -> dict[str, Any]:
        message = self.graph.get_message(message_id)
        if not self.graph._subject_matches(message.subject):
            return {
                "messageId": message.id,
                "subject": message.subject,
                "status": "skipped",
                "reason": "Subject does not match invoice keywords.",
            }
        return self._process_message(message)

    def _process_message(
        self,
        message: MailMessage,
        current_folder: str | None = None,
    ) -> dict[str, Any]:
        attachments = self.graph.list_pdf_attachments(message.id)
        attachment_results = [
            self._process_attachment(attachment).to_dict()
            for attachment in attachments
        ]

        destination = self._destination_for_results(attachment_results)
        moved = False
        if not current_folder or destination.casefold() != current_folder.casefold():
            self.graph.move_message(message.id, destination)
            moved = True
        self._log_mail_message(
            message=message,
            attachment_results=attachment_results,
            current_folder=current_folder,
            destination=destination,
            moved=moved,
        )
        return {
            "messageId": message.id,
            "subject": message.subject,
            "sender": message.sender,
            "receivedDateTime": message.received_date_time,
            "pdfAttachmentCount": len(attachments),
            "destinationFolder": destination,
            "moved": moved,
            "attachments": attachment_results,
        }

    def _process_attachment(self, attachment: MailAttachment) -> AttachmentResult:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / attachment.name
                path.write_bytes(attachment.content)
                extraction = self.parser.extract(path)
            if not extraction["validationPassed"]:
                return AttachmentResult(
                    name=attachment.name,
                    status="manual",
                    invoice_count=extraction["invoiceCount"],
                    validation_passed=False,
                    error="PDF extraction validation failed.",
                )
            sap_results = [
                self.sap.create_supplier_invoice(invoice)
                for invoice in extraction["invoices"]
            ]
            for invoice, sap_result in zip(extraction["invoices"], sap_results):
                self._log_sap_result(invoice, attachment.name, sap_result)
            statuses = {result.get("status", "processed") for result in sap_results}
            attachment_status = "manual" if "manual" in statuses else "processed"
            return AttachmentResult(
                name=attachment.name,
                status=attachment_status,
                invoice_count=extraction["invoiceCount"],
                validation_passed=True,
                sap_results=sap_results,
            )
        except Exception as exc:
            return AttachmentResult(
                name=attachment.name,
                status="error",
                error=str(exc),
            )

    def _destination_for_results(self, results: list[dict[str, Any]]) -> str:
        if not results:
            return self.config.graph.manual_folder
        statuses = {result["status"] for result in results}
        if statuses == {"processed"}:
            return self.config.graph.processed_folder
        if "error" in statuses:
            return self.config.graph.error_folder
        return self.config.graph.manual_folder

    def _log_mail_message(
        self,
        message: MailMessage,
        attachment_results: list[dict[str, Any]],
        current_folder: str | None,
        destination: str,
        moved: bool,
    ) -> None:
        append_activity(
            "mail_read",
            {
                "messageId": message.id,
                "subject": message.subject,
                "sender": message.sender,
                "receivedDateTime": message.received_date_time,
                "mailbox": self.config.graph.mailbox,
                "sourceFolder": current_folder or self.config.graph.source_folder,
                "destinationFolder": destination,
                "moved": moved,
                "pdfAttachmentCount": len(attachment_results),
                "attachments": [
                    {
                        "name": attachment.get("name"),
                        "status": attachment.get("status"),
                        "invoiceCount": attachment.get("invoiceCount"),
                    }
                    for attachment in attachment_results
                ],
            },
        )

    def _log_sap_result(
        self,
        invoice: dict[str, Any],
        attachment_name: str,
        sap_result: dict[str, Any],
    ) -> None:
        append_activity(
            "sap_record",
            {
                "status": sap_result.get("status"),
                "mode": sap_result.get("mode"),
                "posted": sap_result.get("posted"),
                "postingUser": sap_result.get("postingUser"),
                "attachmentName": attachment_name,
                "invoiceNo": invoice.get("invoiceNo"),
                "ettn": invoice.get("ettn"),
                "sellerName": invoice.get("sellerName"),
                "sellerTaxId": invoice.get("sellerTaxId"),
                "buyerTaxId": invoice.get("buyerTaxId"),
                "payableTotal": invoice.get("payableTotal"),
                "currency": invoice.get("currency"),
                "missingMappings": sap_result.get("missingMappings", []),
                "reason": sap_result.get("reason"),
            },
        )
