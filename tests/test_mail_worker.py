from __future__ import annotations

import pytest

from invoice_automation.activity_log import list_activity
from invoice_automation.config import GraphConfig, WorkerConfig
from invoice_automation.graph_client import MailAttachment, MailMessage
from invoice_automation.mail_worker import MailInvoiceWorker
from invoice_automation.mapping import SapMapping
from invoice_automation.sap_client import SapInvoiceClient


class FakeGraph:
    def __init__(self):
        self.moved_to = None
        self.listed_folder = None

    def list_candidate_messages(self, folder_name=None):
        self.listed_folder = folder_name
        return [
            MailMessage(
                id="message-1",
                subject="Sample e-Fatura",
                received_date_time="2026-06-26T18:00:00Z",
                sender="sender@example.com",
            )
        ]

    def list_pdf_attachments(self, message_id: str):
        return [
            MailAttachment(
                name="sample-invoice.pdf",
                content_type="application/pdf",
                content=b"%PDF-1.7 fake test attachment",
            )
        ]

    def move_message(self, message_id: str, destination_folder: str):
        self.moved_to = destination_folder


class FakeParser:
    def extract(self, path):
        return {
            "invoiceCount": 2,
            "validationPassed": True,
            "invoices": [
                _invoice("INV-001", "1000", "200", "1200"),
                _invoice("INV-002", "500", "100", "600"),
            ],
        }


def _invoice(invoice_no: str, net: str, vat: str, payable: str) -> dict:
    return {
        "invoiceNo": invoice_no,
        "ettn": f"00000000-0000-0000-0000-{invoice_no[-3:].zfill(12)}",
        "sellerName": "EXAMPLE SUPPLIER",
        "sellerTaxId": "1111111111",
        "buyerTaxId": "2222222222",
        "netTotal": net,
        "vatTotal": vat,
        "payableTotal": payable,
        "currency": "TRY",
        "validationPassed": True,
        "lines": [
            {
                "lineNo": "1",
                "vatRate": "20",
            }
        ],
    }


@pytest.fixture(autouse=True)
def isolate_activity_log(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_LOG_PATH", str(tmp_path / "activity_log.jsonl"))


def _worker_config() -> WorkerConfig:
    return WorkerConfig(
        graph=GraphConfig(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            mailbox="mailbox@example.com",
            processed_folder="Processed",
            manual_folder="Manual",
            error_folder="Error",
            subject_keywords=("e-Fatura", "Fatura"),
        ),
        sap_mode="dry-run",
    )


def _mapped_sap_client() -> SapInvoiceClient:
    return SapInvoiceClient(
        "dry-run",
        mapping=SapMapping(
            {
                "companyCodes": {"2222222222": "1000"},
                "suppliers": {
                    "1111111111": {
                        "sapSupplierId": "BP1111111111",
                        "glAccount": "7400000000",
                        "costCenter": "CC1000",
                    }
                },
                "taxCodes": {"20": "V1"},
            }
        ),
    )


def test_mail_worker_processes_pdf_attachment_in_dry_run_with_mapping():
    fake_graph = FakeGraph()

    result = MailInvoiceWorker(
        config=_worker_config(),
        graph_client=fake_graph,
        parser=FakeParser(),
        sap_client=_mapped_sap_client(),
    ).run_once()

    assert fake_graph.moved_to == "Processed"
    assert fake_graph.listed_folder == "Inbox"
    assert result["messageCount"] == 1
    attachment = result["processed"][0]["attachments"][0]
    assert attachment["status"] == "processed"
    assert attachment["invoiceCount"] == 2
    assert attachment["validationPassed"] is True
    assert len(attachment["sapResults"]) == 2
    assert attachment["sapResults"][0]["mode"] == "dry-run"
    assert attachment["sapResults"][0]["status"] == "processed"
    assert attachment["sapResults"][0]["resolvedMapping"]["sapSupplierId"] == "BP1111111111"
    assert len(list_activity("mail_read")) == 1
    assert len(list_activity("sap_record")) == 2


def test_mail_worker_routes_missing_mapping_to_manual():
    fake_graph = FakeGraph()

    result = MailInvoiceWorker(
        config=_worker_config(),
        graph_client=fake_graph,
        parser=FakeParser(),
        sap_client=SapInvoiceClient("dry-run", mapping=SapMapping({})),
    ).run_once()

    assert fake_graph.moved_to == "Manual"
    attachment = result["processed"][0]["attachments"][0]
    assert attachment["status"] == "manual"
    first_sap_result = attachment["sapResults"][0]
    assert first_sap_result["status"] == "manual"
    assert "suppliers.1111111111.sapSupplierId" in first_sap_result["missingMappings"]
    assert "companyCodes.2222222222" in first_sap_result["missingMappings"]
    assert "taxCodes.20" in first_sap_result["missingMappings"]


def test_manual_folder_retry_does_not_move_when_still_manual():
    fake_graph = FakeGraph()

    result = MailInvoiceWorker(
        config=_worker_config(),
        graph_client=fake_graph,
        parser=FakeParser(),
        sap_client=SapInvoiceClient("dry-run", mapping=SapMapping({})),
    ).run_folder("Manual")

    assert fake_graph.listed_folder == "Manual"
    assert fake_graph.moved_to is None
    assert result["processed"][0]["moved"] is False
    assert result["processed"][0]["destinationFolder"] == "Manual"
