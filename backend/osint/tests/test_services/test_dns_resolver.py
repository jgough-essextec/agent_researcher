import pytest
from unittest.mock import patch, MagicMock
import dns.resolver
from osint.services.dns_resolver import resolve_dns, DnsRecord, ALLOWED_RECORD_TYPES


def test_raises_on_invalid_domain():
    with pytest.raises(ValueError):
        resolve_dns("not a domain")


def test_blocks_disallowed_record_types():
    records = resolve_dns("acme.com", record_types=["AXFR"])
    assert records == []


def test_allowed_record_types_whitelist():
    assert "A" in ALLOWED_RECORD_TYPES
    assert "MX" in ALLOWED_RECORD_TYPES
    assert "TXT" in ALLOWED_RECORD_TYPES
    assert "AXFR" not in ALLOWED_RECORD_TYPES
    assert "IXFR" not in ALLOWED_RECORD_TYPES


def test_handles_nxdomain_gracefully():
    with patch('dns.resolver.Resolver.resolve', side_effect=dns.resolver.NXDOMAIN):
        records = resolve_dns("doesnotexist12345.com")
    assert records == []


def test_returns_list_of_dns_records():
    mock_rdata = MagicMock()
    mock_rdata.__str__ = lambda self: "10 mail.acme.com."
    mock_answer = [mock_rdata]

    with patch('dns.resolver.Resolver.resolve', return_value=mock_answer):
        records = resolve_dns("acme.com", record_types=["MX"], include_dmarc=False)

    assert isinstance(records, list)
    if records:
        assert isinstance(records[0], DnsRecord)
        assert records[0].record_type == "MX"
