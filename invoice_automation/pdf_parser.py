from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import re
from typing import Any

import fitz
import pdfplumber
from PIL import Image
from pypdf import PdfReader

from .models import ExtractedInvoice, InvoiceLine
from .qr import decode_qr_images, parse_qr_payload, qr_vat_amount
from .utils import clean_text, normalize_key, parse_amount, parse_invoice_date, parse_percent


class EInvoicePdfParser:
    def extract(self, pdf_path: str | Path) -> dict[str, Any]:
        path = Path(pdf_path)
        embedded_xml = self.find_embedded_xml_names(path)
        qr_payloads = self._read_page_qr_payloads(path)
        invoices: list[ExtractedInvoice] = []

        with pdfplumber.open(str(path)) as pdf:
            for page_index, page in enumerate(pdf.pages):
                text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                tables = page.extract_tables() or []
                invoice = self._parse_page(
                    source_file=path.name,
                    source_page=page_index + 1,
                    text=text,
                    tables=tables,
                    qr_payload=qr_payloads.get(page_index + 1),
                )
                invoices.append(invoice)

        return {
            "sourceFile": str(path),
            "embeddedXmlFiles": embedded_xml,
            "invoiceCount": len(invoices),
            "validationPassed": all(inv.validation_passed for inv in invoices),
            "invoices": [inv.to_dict() for inv in invoices],
        }

    def find_embedded_xml_names(self, pdf_path: Path) -> list[str]:
        names: list[str] = []
        reader = PdfReader(str(pdf_path))
        attachments = getattr(reader, "attachments", None)
        if attachments:
            for name in attachments:
                if str(name).lower().endswith(".xml"):
                    names.append(str(name))
        return names

    def _read_page_qr_payloads(self, pdf_path: Path) -> dict[int, dict[str, Any]]:
        doc = fitz.open(str(pdf_path))
        payloads: dict[int, dict[str, Any]] = {}
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            image = self._render_page(page, scale=4)
            width, height = image.size
            qr_crop = image.crop(
                (
                    int(width * 0.73),
                    int(height * 0.03),
                    int(width * 0.97),
                    int(height * 0.22),
                )
            )
            raw = decode_qr_images([qr_crop, image])
            payload = parse_qr_payload(raw)
            if payload:
                payloads[page_index + 1] = payload
        return payloads

    def _render_page(self, page: fitz.Page, scale: int) -> Image.Image:
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        mode = "RGB" if pix.n == 3 else "RGBA"
        return Image.frombytes(mode, (pix.width, pix.height), pix.samples).convert("RGB")

    def _parse_page(
        self,
        source_file: str,
        source_page: int,
        text: str,
        tables: list[list[list[str | None]]],
        qr_payload: dict[str, Any] | None,
    ) -> ExtractedInvoice:
        meta = self._parse_meta_table(tables[0] if len(tables) > 0 else [])
        lines, totals = self._parse_line_table(tables[1] if len(tables) > 1 else [])
        seller_name, buyer_name = self._parse_names(text)
        seller_tax_id, buyer_tax_id, ettn = self._parse_text_ids(text)

        vat_rate_from_qr, vat_amount_from_qr = qr_vat_amount(qr_payload)

        invoice = ExtractedInvoice(
            source_file=source_file,
            source_page=source_page,
            seller_name=seller_name,
            seller_tax_id=(qr_payload or {}).get("vkntckn") or seller_tax_id,
            buyer_name=buyer_name,
            buyer_tax_id=(qr_payload or {}).get("avkntckn") or buyer_tax_id,
            customization_no=meta.get("customization_no"),
            scenario=(qr_payload or {}).get("senaryo") or meta.get("scenario"),
            invoice_type=(qr_payload or {}).get("tip") or meta.get("invoice_type"),
            invoice_no=(qr_payload or {}).get("no") or meta.get("invoice_no"),
            invoice_date=(qr_payload or {}).get("tarih") or parse_invoice_date(meta.get("invoice_date")),
            ettn=(qr_payload or {}).get("ETTN") or ettn,
            currency=(qr_payload or {}).get("parabirimi") or "TRY",
            net_total=parse_amount((qr_payload or {}).get("malhizmettoplam")) or totals.get("net_total"),
            discount_total=totals.get("discount_total"),
            vat_total=vat_amount_from_qr or totals.get("vat_total"),
            gross_total=parse_amount((qr_payload or {}).get("vergidahil")) or totals.get("gross_total"),
            payable_total=parse_amount((qr_payload or {}).get("odenecek")) or totals.get("payable_total"),
            lines=lines,
            qr_payload=qr_payload,
        )
        if vat_rate_from_qr is not None:
            for line in invoice.lines:
                if line.vat_rate is None:
                    line.vat_rate = vat_rate_from_qr
        invoice.validation = self._validate_against_qr(invoice, qr_payload, totals, meta)
        return invoice

    def _parse_meta_table(self, table: list[list[str | None]]) -> dict[str, str]:
        meta: dict[str, str] = {}
        for row in table:
            if len(row) < 2:
                continue
            key = normalize_key(row[0])
            value = clean_text(row[1])
            if not value:
                continue
            if "OZELLESTIRME" in key and "NO" in key:
                meta["customization_no"] = value
            elif key == "SENARYO":
                meta["scenario"] = value
            elif key == "FATURATIPI":
                meta["invoice_type"] = value
            elif key == "FATURANO":
                meta["invoice_no"] = value
            elif key == "FATURATARIHI":
                meta["invoice_date"] = value
        return meta

    def _parse_line_table(
        self, table: list[list[str | None]]
    ) -> tuple[list[InvoiceLine], dict[str, Decimal | None]]:
        lines: list[InvoiceLine] = []
        totals: dict[str, Decimal | None] = {}
        if not table:
            return lines, totals

        for row in table[1:]:
            first = clean_text(row[0] if len(row) > 0 else None)
            if first and first.isdigit():
                lines.append(
                    InvoiceLine(
                        line_no=first,
                        description=clean_text(row[1] if len(row) > 1 else None),
                        quantity=clean_text(row[2] if len(row) > 2 else None),
                        unit_price=parse_amount(row[3] if len(row) > 3 else None),
                        vat_rate=parse_percent(row[6] if len(row) > 6 else None),
                        vat_amount=parse_amount(row[7] if len(row) > 7 else None),
                        net_amount=parse_amount(row[9] if len(row) > 9 else None),
                    )
                )
                continue

            label = clean_text(row[7] if len(row) > 7 else None)
            amount = parse_amount(row[9] if len(row) > 9 else None)
            key = normalize_key(label)
            if not label:
                continue
            if "MALHIZMETTOPLAMTUTARI" in key:
                totals["net_total"] = amount
            elif "TOPLAMISKONTO" in key:
                totals["discount_total"] = amount
            elif "VERGISI" in key:
                totals["vat_total"] = amount
            elif "VERGILERDAHILTOPLAMTUTAR" in key:
                totals["gross_total"] = amount
            elif "ODENECEKTUTAR" in key:
                totals["payable_total"] = amount
        return lines, totals

    def _parse_names(self, text: str) -> tuple[str | None, str | None]:
        lines = [clean_text(line) for line in text.splitlines()]
        lines = [line for line in lines if line]
        seller_name = lines[0] if lines else None
        buyer_name = None
        for index, line in enumerate(lines):
            if normalize_key(line) == "SAYIN" and index + 1 < len(lines):
                buyer_name = lines[index + 1]
                break
        return seller_name, buyer_name

    def _parse_text_ids(self, text: str) -> tuple[str | None, str | None, str | None]:
        tckn_match = re.search(r"TCKN:\s*([0-9]{10,11})", text)
        vkn_match = re.search(r"VKN:\s*([0-9]{10,11})", text)
        ettn_match = re.search(r"ETTN:\s*([0-9a-fA-F-]{36})", text)
        return (
            tckn_match.group(1) if tckn_match else None,
            vkn_match.group(1) if vkn_match else None,
            ettn_match.group(1) if ettn_match else None,
        )

    def _validate_against_qr(
        self,
        invoice: ExtractedInvoice,
        qr_payload: dict[str, Any] | None,
        totals: dict[str, Decimal | None],
        meta: dict[str, str],
    ) -> dict[str, bool]:
        if not qr_payload:
            return {}
        return {
            "sellerTaxId": qr_payload.get("vkntckn") == invoice.seller_tax_id,
            "buyerTaxId": qr_payload.get("avkntckn") == invoice.buyer_tax_id,
            "scenario": qr_payload.get("senaryo") == invoice.scenario,
            "invoiceType": qr_payload.get("tip") == invoice.invoice_type,
            "invoiceNo": qr_payload.get("no") == invoice.invoice_no,
            "invoiceDate": qr_payload.get("tarih") == invoice.invoice_date,
            "ettn": qr_payload.get("ETTN") == invoice.ettn,
            "netTotal": parse_amount(qr_payload.get("malhizmettoplam")) == totals.get("net_total"),
            "vatTotal": invoice.vat_total == totals.get("vat_total"),
            "grossTotal": parse_amount(qr_payload.get("vergidahil")) == totals.get("gross_total"),
            "payableTotal": parse_amount(qr_payload.get("odenecek")) == totals.get("payable_total"),
            "pdfInvoiceNo": meta.get("invoice_no") == invoice.invoice_no,
        }
