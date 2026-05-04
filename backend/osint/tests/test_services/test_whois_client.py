import pytest
from unittest.mock import patch, MagicMock
from osint.services.whois_client import lookup_whois, WhoisResult


def test_raises_on_invalid_domain():
    with pytest.raises(ValueError):
        lookup_whois("not_a_domain!!")


def test_returns_whois_result_dataclass():
    mock_whois = MagicMock()
    mock_whois.registrar = "GoDaddy"
    mock_whois.org = "Acme Corp"
    mock_whois.name = "John Doe"
    mock_whois.creation_date = "2010-01-01"
    mock_whois.expiration_date = "2026-01-01"
    mock_whois.name_servers = ["ns1.example.com", "ns2.example.com"]
    mock_whois.text = "raw whois data..."

    with patch('osint.services.whois_client.whois.whois', return_value=mock_whois):
        result = lookup_whois("acme.com")

    assert isinstance(result, WhoisResult)
    assert result.registrar == "GoDaddy"
    assert result.registrant_org == "Acme Corp"
    assert len(result.name_servers) == 2


def test_handles_whois_failure_gracefully():
    with patch('osint.services.whois_client.whois.whois', side_effect=Exception("connection timeout")):
        result = lookup_whois("acme.com")
    assert isinstance(result, WhoisResult)
    assert result.registrar == ""
    assert result.error != ""
