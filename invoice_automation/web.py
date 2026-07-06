from __future__ import annotations

from pathlib import Path
import os
import tempfile
import threading
import time

from flask import Flask, Response, jsonify, request
from flask import send_from_directory

from . import __version__
from .activity_log import clear_activity, list_activity
from .config import WorkerConfig
from .config import GraphConfig
from .mail_worker import MailInvoiceWorker
from .mapping import mapping_path, read_mapping_data, write_mapping_data
from .pdf_parser import EInvoicePdfParser
from .runtime_settings import (
    public_settings,
    read_settings_data,
    setting_bool,
    setting_int,
    settings_path,
    write_settings_data,
)


app = Flask(__name__)
_mail_poller_started = False
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "web" / "dist"


@app.get("/")
def frontend_index():
    if not FRONTEND_DIST.joinpath("index.html").exists():
        return jsonify({"status": "frontend-not-built"}), 404
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.get("/assets/<path:filename>")
def frontend_assets(filename: str):
    return send_from_directory(FRONTEND_DIST / "assets", filename)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "version": __version__})


@app.post("/api/extract")
def extract_pdf():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify({"error": "Missing multipart file field named 'file'."}), 400
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / (uploaded.filename or "invoice.pdf")
        uploaded.save(path)
        result = EInvoicePdfParser().extract(path)
    return jsonify(result)


@app.get("/api/settings")
def get_settings():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    return jsonify(
        {
            "source": str(settings_path()),
            "data": public_settings(read_settings_data()),
        }
    )


@app.put("/api/settings")
def put_settings():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Settings payload must be a JSON object."}), 400
    saved = write_settings_data(payload)
    _start_mail_poller_once()
    return jsonify(
        {
            "saved": True,
            "source": str(settings_path()),
            "data": public_settings(saved),
        }
    )


@app.get("/api/logs")
def get_logs():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    event_type = request.args.get("type") or None
    limit = request.args.get("limit", "100")
    try:
        limit_value = min(max(int(limit), 1), 1000)
    except ValueError:
        limit_value = 100
    return jsonify(
        {
            "type": event_type,
            "source": "activity_log",
            "items": list_activity(event_type=event_type, limit=limit_value),
        }
    )


@app.delete("/api/logs")
def delete_logs():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    event_type = request.args.get("type") or None
    return jsonify({"deleted": clear_activity(event_type=event_type), "type": event_type})


@app.get("/api/mapping")
def get_mapping():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    return jsonify(
        {
            "source": "SAP_MAPPING_JSON" if os.getenv("SAP_MAPPING_JSON") else str(mapping_path()),
            "readOnly": bool(os.getenv("SAP_MAPPING_JSON")),
            "data": read_mapping_data(),
        }
    )


@app.put("/api/mapping")
def put_mapping():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    if os.getenv("SAP_MAPPING_JSON"):
        return jsonify({"error": "SAP_MAPPING_JSON is configured; file mapping is read-only."}), 409
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Mapping payload must be a JSON object."}), 400
    path = write_mapping_data(payload)
    return jsonify({"saved": True, "source": str(path), "data": payload})


@app.post("/jobs/process-mail")
def process_mail():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    try:
        result = MailInvoiceWorker(WorkerConfig.from_env()).run_once()
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/jobs/process-manual")
def process_manual():
    auth_error = _check_worker_secret()
    if auth_error:
        return auth_error
    try:
        config = WorkerConfig.from_env()
        result = MailInvoiceWorker(config).run_folder(config.graph.manual_folder)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/graph/notifications")
def graph_notifications():
    validation_token = request.args.get("validationToken")
    if validation_token is not None:
        return Response(validation_token, status=200, content_type="text/plain")

    payload = request.get_json(silent=True) or {}
    notifications = payload.get("value", [])
    valid_notifications = [
        notification
        for notification in notifications
        if _valid_graph_client_state(notification)
    ]
    if valid_notifications:
        thread = threading.Thread(
            target=_process_graph_notifications,
            args=(valid_notifications,),
            daemon=True,
        )
        thread.start()
    return jsonify({"accepted": len(valid_notifications)}), 202


def _check_worker_secret():
    expected = os.getenv("WORKER_SHARED_SECRET")
    if not expected:
        return jsonify({"error": "WORKER_SHARED_SECRET is not configured."}), 503
    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {expected}":
        return jsonify({"error": "Unauthorized."}), 401
    return None


def _valid_graph_client_state(notification: dict) -> bool:
    expected = os.getenv("GRAPH_WEBHOOK_CLIENT_STATE") or os.getenv("WORKER_SHARED_SECRET")
    if not expected:
        return False
    return notification.get("clientState") == expected


def _process_graph_notifications(notifications: list[dict]) -> None:
    try:
        worker = MailInvoiceWorker(WorkerConfig.from_env())
        for notification in notifications:
            if notification.get("changeType") != "created":
                continue
            message_id = (notification.get("resourceData") or {}).get("id")
            if not message_id:
                continue
            worker.process_message_id(message_id)
    except Exception as exc:
        app.logger.exception("Graph notification processing failed: %s", exc)


def _start_mail_poller_once() -> None:
    global _mail_poller_started
    if _mail_poller_started:
        return
    if not setting_bool("mailPollerEnabled", "MAIL_POLLER_ENABLED", False):
        return

    try:
        GraphConfig.from_env()
    except ValueError as exc:
        app.logger.warning(
            "Mail poller is enabled but disabled for this start; %s",
            exc,
        )
        return

    _mail_poller_started = True
    thread = threading.Thread(target=_mail_poller_loop, daemon=True)
    thread.start()


def _mail_poller_loop() -> None:
    while True:
        interval = max(setting_int("mailPollIntervalSeconds", "MAIL_POLL_INTERVAL_SECONDS", 300), 30)
        if not setting_bool("mailPollerEnabled", "MAIL_POLLER_ENABLED", False):
            time.sleep(interval)
            continue
        try:
            result = MailInvoiceWorker(WorkerConfig.from_env()).run_once()
            app.logger.info(
                "Mail poller completed; messageCount=%s",
                result.get("messageCount"),
            )
        except Exception as exc:
            app.logger.exception("Mail poller failed: %s", exc)
        time.sleep(interval)


_start_mail_poller_once()
