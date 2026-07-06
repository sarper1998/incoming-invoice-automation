from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import os
import sys

from .config import GraphConfig
from .graph_client import GraphClient
from .pdf_parser import EInvoicePdfParser


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="invoice-extract")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract", help="Extract invoices from a PDF file.")
    extract.add_argument("pdf", help="Input PDF path.")
    extract.add_argument("--output", "-o", help="Output file path. Defaults to stdout.")
    extract.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format.",
    )

    subscribe = subparsers.add_parser(
        "subscribe",
        help="Create a Microsoft Graph message webhook subscription.",
    )
    subscribe.add_argument("--notification-url", required=True)
    subscribe.add_argument("--client-state")
    subscribe.add_argument("--expiration-days", type=int, default=6)

    args = parser.parse_args(argv)
    if args.command == "extract":
        result = EInvoicePdfParser().extract(args.pdf)
        output = _format_result(result, args.format)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            encoding = "utf-8-sig" if args.format == "csv" else "utf-8"
            output_path.write_text(output, encoding=encoding, newline="")
        else:
            sys.stdout.write(output)
            if not output.endswith("\n"):
                sys.stdout.write("\n")
        return 0

    if args.command == "subscribe":
        client_state = (
            args.client_state
            or os.getenv("GRAPH_WEBHOOK_CLIENT_STATE")
            or os.getenv("WORKER_SHARED_SECRET")
        )
        if not client_state:
            raise SystemExit("Missing --client-state or GRAPH_WEBHOOK_CLIENT_STATE.")
        result = GraphClient(GraphConfig.from_env()).create_message_subscription(
            notification_url=args.notification_url,
            client_state=client_state,
            expiration_days=args.expiration_days,
        )
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
        return 0

    parser.error("Unknown command")
    return 0


def _format_result(result: dict, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)

    rows = []
    for invoice in result["invoices"]:
        first_line = invoice["lines"][0] if invoice["lines"] else {}
        rows.append(
            {
                "sourcePage": invoice["sourcePage"],
                "invoiceNo": invoice["invoiceNo"],
                "invoiceDate": invoice["invoiceDate"],
                "ettn": invoice["ettn"],
                "sellerTaxId": invoice["sellerTaxId"],
                "buyerTaxId": invoice["buyerTaxId"],
                "description": first_line.get("description"),
                "netTotal": invoice["netTotal"],
                "vatTotal": invoice["vatTotal"],
                "payableTotal": invoice["payableTotal"],
                "validationPassed": invoice["validationPassed"],
            }
        )
    if not rows:
        return ""
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


if __name__ == "__main__":
    raise SystemExit(main())
