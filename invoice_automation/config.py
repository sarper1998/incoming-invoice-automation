from __future__ import annotations

from dataclasses import dataclass
import os

from .runtime_settings import read_settings_data, setting_int, setting_value


@dataclass(frozen=True)
class GraphConfig:
    tenant_id: str
    client_id: str
    client_secret: str
    mailbox: str
    source_folder: str = "Inbox"
    processed_folder: str = "Processed"
    manual_folder: str = "Manual"
    error_folder: str = "Error"
    max_messages: int = 10
    subject_keywords: tuple[str, ...] = ("e-Fatura", "e-Arsiv", "Fatura")

    @classmethod
    def from_env(cls) -> "GraphConfig":
        settings = read_settings_data()
        missing = [
            display_name
            for key, env_name, display_name in (
                ("graphTenantId", "GRAPH_TENANT_ID", "GRAPH_TENANT_ID"),
                ("graphClientId", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_ID"),
                ("graphClientSecret", "GRAPH_CLIENT_SECRET", "GRAPH_CLIENT_SECRET"),
                ("graphMailbox", "GRAPH_MAILBOX", "GRAPH_MAILBOX"),
            )
            if not setting_value(key, env_name)
        ]
        if missing:
            raise ValueError("Missing required Graph settings: " + ", ".join(missing))
        return cls(
            tenant_id=setting_value("graphTenantId", "GRAPH_TENANT_ID"),
            client_id=setting_value("graphClientId", "GRAPH_CLIENT_ID"),
            client_secret=setting_value("graphClientSecret", "GRAPH_CLIENT_SECRET"),
            mailbox=setting_value("graphMailbox", "GRAPH_MAILBOX"),
            source_folder=setting_value("graphSourceFolder", "GRAPH_SOURCE_FOLDER", "Inbox"),
            processed_folder=setting_value("graphProcessedFolder", "GRAPH_PROCESSED_FOLDER", "Processed"),
            manual_folder=setting_value("graphManualFolder", "GRAPH_MANUAL_FOLDER", "Manual"),
            error_folder=setting_value("graphErrorFolder", "GRAPH_ERROR_FOLDER", "Error"),
            max_messages=setting_int("graphMaxMessages", "GRAPH_MAX_MESSAGES", 10),
            subject_keywords=tuple(
                keyword.strip()
                for keyword in str(
                    settings.get("graphSubjectKeywords")
                    or os.getenv("GRAPH_SUBJECT_KEYWORDS")
                    or "e-Fatura,e-Arsiv,Fatura"
                ).split(",")
                if keyword.strip()
            ),
        )


@dataclass(frozen=True)
class WorkerConfig:
    graph: GraphConfig
    sap_mode: str = "dry-run"
    sap_posting_user: str | None = None

    @classmethod
    def from_env(cls) -> "WorkerConfig":
        return cls(
            graph=GraphConfig.from_env(),
            sap_mode=str(setting_value("sapMode", "SAP_MODE", "dry-run")).lower(),
            sap_posting_user=setting_value("sapPostingUser", "SAP_POSTING_USER"),
        )
