import pytest
from osint.services.dns_resolver import DnsRecord
from osint.services.email_security import assess_email_security, EmailSecurityResult


def _txt(domain, values):
    return DnsRecord(domain=domain, record_type="TXT", values=tuple(values))

def _dmarc(domain, value):
    return DnsRecord(domain=f"_dmarc.{domain}", record_type="DMARC", values=(value,))

def _mx(domain, values):
    return DnsRecord(domain=domain, record_type="MX", values=tuple(values))


def test_returns_immutable_dataclass():
    result = assess_email_security("acme.com", [])
    assert isinstance(result, EmailSecurityResult)
    with pytest.raises(Exception):
        result.has_spf = True  # frozen dataclass


def test_missing_spf_and_dmarc_grades_f():
    result = assess_email_security("acme.com", [])
    assert result.has_spf is False
    assert result.has_dmarc is False
    assert result.overall_grade == "F"


def test_spf_present_dmarc_reject_grades_a():
    records = [
        _txt("acme.com", ["v=spf1 include:_spf.google.com -all"]),
        _dmarc("acme.com", "v=DMARC1; p=reject; rua=mailto:dmarc@acme.com"),
    ]
    result = assess_email_security("acme.com", records)
    assert result.has_spf is True
    assert result.has_dmarc is True
    assert result.dmarc_policy == "reject"
    assert result.overall_grade in ("A", "B")


def test_dmarc_none_policy():
    records = [
        _txt("acme.com", ["v=spf1 include:_spf.google.com ~all"]),
        _dmarc("acme.com", "v=DMARC1; p=none"),
    ]
    result = assess_email_security("acme.com", records)
    assert result.dmarc_policy == "none"
    assert result.overall_grade in ("C", "D")


def test_missing_dmarc_grades_d_or_f():
    records = [_txt("acme.com", ["v=spf1 include:_spf.google.com ~all"])]
    result = assess_email_security("acme.com", records)
    assert result.has_dmarc is False
    assert result.dmarc_policy == "missing"
    assert result.overall_grade in ("D", "F")


def test_identifies_google_mx_provider():
    records = [_mx("acme.com", ["10 acme-com.mail.protection.outlook.com."])]
    result = assess_email_security("acme.com", records)
    providers_str = " ".join(result.mx_providers)
    assert any(word in providers_str for word in ("Microsoft", "Exchange", "Office", "365", "Outlook"))
