from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import re

TR_TO_ASCII = str.maketrans(
    {
        "ç": "c",
        "Ç": "C",
        "ğ": "g",
        "Ğ": "G",
        "ı": "i",
        "I": "I",
        "İ": "I",
        "ö": "o",
        "Ö": "O",
        "ş": "s",
        "Ş": "S",
        "ü": "u",
        "Ü": "U",
    }
)


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value.replace("\n", " ")).strip()


def normalize_key(value: str | None) -> str:
    if not value:
        return ""
    value = value.translate(TR_TO_ASCII).upper()
    return re.sub(r"[^A-Z0-9]+", "", value)


def parse_amount(value: str | int | float | Decimal | None) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value)
    text = text.replace("TRY", "").replace("TL", "").replace("%", "").strip()
    text = re.sub(r"[^0-9,.\-]", "", text)
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_percent(value: str | None) -> Decimal | None:
    return parse_amount(value)


def parse_invoice_date(value: str | None) -> str | None:
    value = clean_text(value)
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return value
