from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_MAPPING_PATH = Path("config/sap_mapping.json")


@dataclass(frozen=True)
class MappingResolution:
    values: dict[str, Any]
    missing: list[str]
    suggested_mapping: dict[str, Any]

    @property
    def complete(self) -> bool:
        return not self.missing


class SapMapping:
    def __init__(self, data: dict[str, Any] | None = None):
        self.data = data or {}

    @classmethod
    def from_env(cls) -> "SapMapping":
        raw = os.getenv("SAP_MAPPING_JSON")
        if raw:
            return cls(json.loads(raw))

        path = mapping_path()
        if path.exists():
            return cls(json.loads(path.read_text(encoding="utf-8")))
        return cls()

    def resolve(self, invoice: dict[str, Any]) -> MappingResolution:
        seller_tax_id = invoice.get("sellerTaxId")
        buyer_tax_id = invoice.get("buyerTaxId")
        supplier = self.data.get("suppliers", {}).get(seller_tax_id or "", {})

        values = {
            "companyCode": self._company_code(buyer_tax_id),
            "sapSupplierId": supplier.get("sapSupplierId"),
            "glAccount": supplier.get("glAccount") or self.data.get("defaultGlAccount"),
            "costCenter": supplier.get("costCenter") or self.data.get("defaultCostCenter"),
            "paymentTerms": supplier.get("paymentTerms") or self.data.get("defaultPaymentTerms"),
            "documentType": self.data.get("documentType"),
            "postingMode": self.data.get("postingMode"),
            "lineTaxCodes": self._line_tax_codes(invoice, supplier),
        }

        missing = self._missing_fields(invoice, seller_tax_id, buyer_tax_id, values)
        return MappingResolution(
            values=values,
            missing=missing,
            suggested_mapping=self._suggested_mapping(invoice),
        )

    def _company_code(self, buyer_tax_id: str | None) -> str | None:
        by_tax_id = self.data.get("companyCodes", {})
        return by_tax_id.get(buyer_tax_id or "") or self.data.get("companyCode")

    def _line_tax_codes(
        self,
        invoice: dict[str, Any],
        supplier: dict[str, Any],
    ) -> list[dict[str, str | None]]:
        results = []
        tax_codes = self.data.get("taxCodes", {})
        for line in invoice.get("lines", []):
            rate = _rate_key(line.get("vatRate"))
            results.append(
                {
                    "lineNo": line.get("lineNo"),
                    "vatRate": rate,
                    "taxCode": (
                        tax_codes.get(rate)
                        or supplier.get("taxCode")
                        or self.data.get("defaultTaxCode")
                    ),
                }
            )
        return results

    def _missing_fields(
        self,
        invoice: dict[str, Any],
        seller_tax_id: str | None,
        buyer_tax_id: str | None,
        values: dict[str, Any],
    ) -> list[str]:
        missing = []
        if not seller_tax_id:
            missing.append("invoice.sellerTaxId")
        if seller_tax_id and not values["sapSupplierId"]:
            missing.append(f"suppliers.{seller_tax_id}.sapSupplierId")
        if not buyer_tax_id:
            missing.append("invoice.buyerTaxId")
        if buyer_tax_id and not values["companyCode"]:
            missing.append(f"companyCodes.{buyer_tax_id}")
        if not values["glAccount"]:
            missing.append(f"suppliers.{seller_tax_id or '<sellerTaxId>'}.glAccount")

        if not invoice.get("lines"):
            missing.append("invoice.lines")
        for line_tax in values["lineTaxCodes"]:
            if not line_tax["taxCode"]:
                missing.append(f"taxCodes.{line_tax['vatRate'] or '<vatRate>'}")
        return missing

    def _suggested_mapping(self, invoice: dict[str, Any]) -> dict[str, Any]:
        seller_tax_id = invoice.get("sellerTaxId") or "<sellerTaxId>"
        buyer_tax_id = invoice.get("buyerTaxId") or "<buyerTaxId>"
        rates = sorted(
            {
                _rate_key(line.get("vatRate")) or "<vatRate>"
                for line in invoice.get("lines", [])
            }
        )
        return {
            "companyCodes": {buyer_tax_id: ""},
            "suppliers": {
                seller_tax_id: {
                    "name": invoice.get("sellerName"),
                    "sapSupplierId": "",
                    "glAccount": "",
                    "costCenter": "",
                    "taxCode": "",
                    "paymentTerms": "",
                }
            },
            "taxCodes": {rate: "" for rate in rates},
        }


def _rate_key(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def mapping_path() -> Path:
    return Path(os.getenv("SAP_MAPPING_PATH", DEFAULT_MAPPING_PATH))


def read_mapping_data() -> dict[str, Any]:
    raw = os.getenv("SAP_MAPPING_JSON")
    if raw:
        return json.loads(raw)

    path = mapping_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def write_mapping_data(data: dict[str, Any]) -> Path:
    path = mapping_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
