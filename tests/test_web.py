import pytest

from invoice_automation.activity_log import append_activity
from invoice_automation.web import app


@pytest.fixture(autouse=True)
def isolate_runtime_files(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_SETTINGS_PATH", str(tmp_path / "runtime_settings.json"))
    monkeypatch.setenv("APP_LOG_PATH", str(tmp_path / "activity_log.jsonl"))
    monkeypatch.delenv("WORKER_SHARED_SECRET", raising=False)
    monkeypatch.delenv("SAP_MAPPING_JSON", raising=False)


def test_extract_requires_worker_secret_when_unconfigured():
    client = app.test_client()

    response = client.post("/api/extract")

    assert response.status_code == 503
    assert response.json["error"] == "WORKER_SHARED_SECRET is not configured."


def test_mapping_can_be_saved_with_worker_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKER_SHARED_SECRET", "test-secret")
    monkeypatch.delenv("SAP_MAPPING_JSON", raising=False)
    monkeypatch.setenv("SAP_MAPPING_PATH", str(tmp_path / "sap_mapping.json"))
    client = app.test_client()

    save_response = client.put(
        "/api/mapping",
        headers={"Authorization": "Bearer test-secret"},
        json={"companyCodes": {"2222222222": "1000"}},
    )
    read_response = client.get(
        "/api/mapping",
        headers={"Authorization": "Bearer test-secret"},
    )

    assert save_response.status_code == 200
    assert save_response.json["saved"] is True
    assert read_response.status_code == 200
    assert read_response.json["data"]["companyCodes"]["2222222222"] == "1000"


def test_settings_can_be_saved_and_masks_secrets(monkeypatch):
    monkeypatch.setenv("WORKER_SHARED_SECRET", "test-secret")
    client = app.test_client()

    save_response = client.put(
        "/api/settings",
        headers={"Authorization": "Bearer test-secret"},
        json={
            "graphTenantId": "tenant",
            "graphClientId": "client",
            "graphClientSecret": "graph-secret",
            "graphMailbox": "invoice@example.com",
            "graphSourceFolder": "e-Fatura",
            "mailPollerEnabled": False,
            "sapPostingUser": "SAP_API_USER",
        },
    )
    read_response = client.get(
        "/api/settings",
        headers={"Authorization": "Bearer test-secret"},
    )

    assert save_response.status_code == 200
    assert save_response.json["data"]["graphMailbox"] == "invoice@example.com"
    assert save_response.json["data"]["graphClientSecret"] == ""
    assert save_response.json["data"]["graphClientSecretConfigured"] is True
    assert read_response.json["data"]["sapPostingUser"] == "SAP_API_USER"


def test_logs_can_be_listed_and_cleared_by_type(monkeypatch):
    monkeypatch.setenv("WORKER_SHARED_SECRET", "test-secret")
    append_activity("mail_read", {"subject": "e-Fatura", "mailbox": "invoice@example.com"})
    append_activity("sap_record", {"invoiceNo": "ABC", "status": "manual"})
    client = app.test_client()

    mail_response = client.get(
        "/api/logs?type=mail_read",
        headers={"Authorization": "Bearer test-secret"},
    )
    delete_response = client.delete(
        "/api/logs?type=mail_read",
        headers={"Authorization": "Bearer test-secret"},
    )
    sap_response = client.get(
        "/api/logs?type=sap_record",
        headers={"Authorization": "Bearer test-secret"},
    )

    assert mail_response.status_code == 200
    assert len(mail_response.json["items"]) == 1
    assert delete_response.json["deleted"] == 1
    assert len(sap_response.json["items"]) == 1
