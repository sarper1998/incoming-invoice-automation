from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


def _money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


@dataclass
class InvoiceLine:
    line_no: str | None = None
    description: str | None = None
    quantity: str | None = None
    unit_price: Decimal | None = None
    vat_rate: Decimal | None = None
    vat_amount: Decimal | None = None
    net_amount: Decimal | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineNo": self.line_no,
            "description": self.description,
            "quantity": self.quantity,
            "unitPrice": _money(self.unit_price),
            "vatRate": _money(self.vat_rate),
            "vatAmount": _money(self.vat_amount),
            "netAmount": _money(self.net_amount),
        }


@dataclass
class ExtractedInvoice:
    source_file: str
    source_page: int
    seller_name: str | None = None
    seller_tax_id: str | None = None
    buyer_name: str | None = None
    buyer_tax_id: str | None = None
    customization_no: str | None = None
    scenario: str | None = None
    invoice_type: str | None = None
    invoice_no: str | None = None
    invoice_date: str | None = None
    ettn: str | None = None
    currency: str | None = None
    net_total: Decimal | None = None
    discount_total: Decimal | None = None
    vat_total: Decimal | None = None
    gross_total: Decimal | None = None
    payable_total: Decimal | None = None
    lines: list[InvoiceLine] = field(default_factory=list)
    qr_payload: dict[str, Any] | None = None
    validation: dict[str, bool] = field(default_factory=dict)

    @property
    def validation_passed(self) -> bool:
        return bool(self.validation) and all(self.validation.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceFile": self.source_file,
            "sourcePage": self.source_page,
            "sellerName": self.seller_name,
            "sellerTaxId": self.seller_tax_id,
            "buyerName": self.buyer_name,
            "buyerTaxId": self.buyer_tax_id,
            "customizationNo": self.customization_no,
            "scenario": self.scenario,
            "invoiceType": self.invoice_type,
            "invoiceNo": self.invoice_no,
            "invoiceDate": self.invoice_date,
            "ettn": self.ettn,
            "currency": self.currency,
            "netTotal": _money(self.net_total),
            "discountTotal": _money(self.discount_total),
            "vatTotal": _money(self.vat_total),
            "grossTotal": _money(self.gross_total),
            "payableTotal": _money(self.payable_total),
            "lines": [line.to_dict() for line in self.lines],
            "qrPayload": self.qr_payload,
            "validation": self.validation,
            "validationPassed": self.validation_passed,
        }
