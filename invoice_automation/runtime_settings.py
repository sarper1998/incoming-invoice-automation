from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS_PATH = Path("data/runtime_settings.json")
SECRET_FIELDS = {"graphClientSecret", "sapClientSecret"}
ENV_NAMES = {
    "graphTenantId": "GRAPH_TENANT_ID",
    "graphClientId": "GRAPH_CLIENT_ID",
    "graphClientSecret": "GRAPH_CLIENT_SECRET",
    "graphMailbox": "GRAPH_MAILBOX",
    "graphSourceFolder": "GRAPH_SOURCE_FOLDER",
    "graphProcessedFolder": "GRAPH_PROCESSED_FOLDER",
    "graphManualFolder": "GRAPH_MANUAL_FOLDER",
    "graphErrorFolder": "GRAPH_ERROR_FOLDER",
    "graphMaxMessages": "GRAPH_MAX_MESSAGES",
    "graphSubjectKeywords": "GRAPH_SUBJECT_KEYWORDS",
    "mailPollerEnabled": "MAIL_POLLER_ENABLED",
    "mailPollIntervalSeconds": "MAIL_POLL_INTERVAL_SECONDS",
    "sapMode": "SAP_MODE",
    "sapBaseUrl": "SAP_BASE_URL",
    "sapAuthUrl": "SAP_AUTH_URL",
    "sapClientId": "SAP_CLIENT_ID",
    "sapClientSecret": "SAP_CLIENT_SECRET",
    "sapPostingUser": "SAP_POSTING_USER",
}
DEFAULT_SETTINGS: dict[str, Any] = {
    "graphTenantId": "",
    "graphClientId": "",
    "graphClientSecret": "",
    "graphMailbox": "",
    "graphSourceFolder": "Inbox",
    "graphProcessedFolder": "Processed",
    "graphManualFolder": "Manual",
    "graphErrorFolder": "Error",
    "graphMaxMessages": 10,
    "graphSubjectKeywords": "e-Fatura,e-Arsiv,Fatura",
    "mailPollerEnabled": True,
    "mailPollIntervalSeconds": 300,
    "sapMode": "dry-run",
    "sapBaseUrl": "",
    "sapAuthUrl": "",
    "sapClientId": "",
    "sapClientSecret": "",
    "sapPostingUser": "",
}


def settings_path() -> Path:
    return Path(os.getenv("APP_SETTINGS_PATH", DEFAULT_SETTINGS_PATH))


def read_settings_data() -> dict[str, Any]:
    data = deepcopy(DEFAULT_SETTINGS)
    for key, env_name in ENV_NAMES.items():
        env_value = os.getenv(env_name)
        if env_value not in (None, ""):
            data[key] = env_value
    data.update(_read_stored_settings())
    return _coerce_settings(data)


def _read_stored_settings() -> dict[str, Any]:
    path = settings_path()
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(stored, dict):
            return stored
    return {}


def write_settings_data(payload: dict[str, Any]) -> dict[str, Any]:
    current = _read_stored_settings()
    sanitized = _normalize_settings(payload, current)
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return sanitized


def public_settings(data: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = deepcopy(data or read_settings_data())
    for field in SECRET_FIELDS:
        has_value = bool(settings.get(field))
        settings[field] = ""
        settings[f"{field}Configured"] = has_value
    return settings


def setting_value(key: str, env_name: str, default: Any = None) -> Any:
    settings = read_settings_data()
    value = settings.get(key)
    if value not in (None, ""):
        return value
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value
    return default


def setting_bool(key: str, env_name: str, default: bool = False) -> bool:
    value = setting_value(key, env_name, default)
    if isinstance(value, bool):
        return value
    return str(value).casefold() in {"1", "true", "yes", "on"}


def setting_int(key: str, env_name: str, default: int) -> int:
    value = setting_value(key, env_name, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_settings(payload: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    data = deepcopy(DEFAULT_SETTINGS)
    data.update(current)
    for key in DEFAULT_SETTINGS:
        if key not in payload:
            continue
        value = payload[key]
        if key in SECRET_FIELDS and value == "":
            continue
        data[key] = value

    return _coerce_settings(data)


def _coerce_settings(data: dict[str, Any]) -> dict[str, Any]:
    data = deepcopy(data)
    data["graphMaxMessages"] = max(_to_int(data.get("graphMaxMessages"), 10), 1)
    data["mailPollIntervalSeconds"] = max(_to_int(data.get("mailPollIntervalSeconds"), 300), 30)
    data["mailPollerEnabled"] = _to_bool(data.get("mailPollerEnabled"))
    data["sapMode"] = str(data.get("sapMode") or "dry-run").lower()
    return data


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).casefold() in {"1", "true", "yes", "on"}
