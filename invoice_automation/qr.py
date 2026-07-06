from __future__ import annotations

from decimal import Decimal
import json
import re
from typing import Any

from PIL import Image, ImageOps
import zxingcpp


def decode_qr_images(images: list[Image.Image]) -> str | None:
    for image in images:
        for candidate in _image_variants(image):
            barcodes = zxingcpp.read_barcodes(candidate)
            if barcodes:
                return barcodes[0].text
    return None


def parse_qr_payload(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < 0:
        return None
    payload = raw[start : end + 1]
    payload = re.sub(r",\s*}", "}", payload)
    return json.loads(payload)


def qr_vat_amount(payload: dict[str, Any] | None) -> tuple[Decimal | None, Decimal | None]:
    if not payload:
        return None, None
    for key, value in payload.items():
        match = re.fullmatch(r"hesaplanankdv\((\d+(?:[.,]\d+)?)\)", key)
        if match:
            return Decimal(match.group(1).replace(",", ".")), Decimal(str(value))
    return None, None


def _image_variants(image: Image.Image) -> list[Image.Image]:
    rgb = image.convert("RGB")
    gray = ImageOps.grayscale(rgb)
    autocontrast = ImageOps.autocontrast(gray)
    threshold = autocontrast.point(lambda pixel: 255 if pixel > 170 else 0).convert("RGB")
    enlarged = autocontrast.resize(
        (autocontrast.width * 2, autocontrast.height * 2),
        Image.Resampling.NEAREST,
    )
    enlarged_threshold = enlarged.point(lambda pixel: 255 if pixel > 170 else 0).convert("RGB")
    return [rgb, autocontrast.convert("RGB"), threshold, enlarged_threshold]
