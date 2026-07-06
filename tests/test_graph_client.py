from invoice_automation.config import GraphConfig
from invoice_automation.graph_client import GraphClient


def test_subject_keyword_filter_is_case_insensitive():
    client = GraphClient(
        GraphConfig(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            mailbox="mailbox@example.com",
            subject_keywords=("e-Fatura", "e-Arşiv", "Fatura"),
        )
    )

    assert client._subject_matches("e-Fatura")
    assert client._subject_matches("Yeni E-FATURA bildirimi")
    assert client._subject_matches("Fatura ektedir")
    assert not client._subject_matches("Banka dekontu")
