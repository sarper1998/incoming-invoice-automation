import os
from pathlib import Path

import pytest

from invoice_automation.pdf_parser import EInvoicePdfParser


def _private_sample_pdf() -> Path:
    configured = os.getenv("PRIVATE_INVOICE_SAMPLE_PDF")
    path = Path(configured) if configured else Path(__file__).resolve().parents[1] / "private-invoice-sample.pdf"
    if not path.exists():
        pytest.skip("Private invoice PDF sample is not included in the public repository.")
    return path


def test_private_invoice_pdf_extracts_invoices():
    pdf_path = _private_sample_pdf()

    result = EInvoicePdfParser().extract(pdf_path)

    assert result["embeddedXmlFiles"] == []
    assert result["invoiceCount"] >= 1
    assert result["validationPassed"] is True

    invoices = result["invoices"]
    assert invoices[0]["invoiceNo"]
    assert invoices[0]["sellerTaxId"]
    assert invoices[0]["buyerTaxId"]
    assert invoices[0]["payableTotal"]


def test_private_invoice_qr_and_pdf_fields_match():
    pdf_path = _private_sample_pdf()

    invoice = EInvoicePdfParser().extract(pdf_path)["invoices"][0]

    assert invoice["invoiceDate"]
    assert invoice["ettn"]
    assert invoice["netTotal"]
    assert invoice["vatTotal"]
    assert invoice["payableTotal"]
    assert invoice["validationPassed"] is True
    assert all(invoice["validation"].values())
