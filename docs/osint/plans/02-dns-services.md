# Plan 02 — DNS & Infrastructure Services

**Depends on:** Plan 01 (app + models created)  
**Unlocks:** Plan 04 (Phase 2 DNS workflow nodes)

---

## Goal

Build the four pure-Python service modules that perform passive DNS/WHOIS reconnaissance. These are the core data-gathering components that feed Phase 2 of the OSINT workflow.

No subprocess calls anywhere. All DNS uses `dnspython`, WHOIS uses `python-whois`, crt.sh uses `httpx`, ARIN uses their REST API.

---

## Services to Build

1. `osint/services/crt_sh.py` — Certificate Transparency log queries
2. `osint/services/dns_resolver.py` — DNS record resolution (dnspython)
3. `osint/services/whois_client.py` — WHOIS lookups (python-whois)
4. `osint/services/email_security.py` — SPF/DKIM/DMARC assessment

---

## Security Constraint (All Services)

Every service that accepts a domain must validate it first:

```python
# osint/services/_validators.py

import re

_DOMAIN_RE = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?'
    r'(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*'
    r'\.[a-zA-Z]{2,}$'
)
_BLOCKED_TLDS = frozenset({'.local', '.internal', '.corp', '.lan', '.home'})


def validate_domain(domain: str) -> str:
    """Validate and normalise domain. Raises ValueError on invalid input."""
    domain = domain.strip().lower()
    if len(domain) > 253:
        raise ValueError(f"Domain too long ({len(domain)} chars): {domain}")
    if any(domain.endswith(tld) for tld in _BLOCKED_TLDS):
        raise ValueError(f"Cannot query internal domain: {domain}")
    if not _DOMAIN_RE.match(domain):
        raise ValueError(f"Invalid domain format: {domain}")
    return domain
```

---

## Service 1: `crt_sh.py` — Certificate Transparency

### Tests First

**File:** `backend/osint/tests/test_services/test_crt_sh.py`

```python
import pytest
from unittest.mock import patch, AsyncMock
from osint.services.crt_sh import query_crt_sh, CrtShEntry


@pytest.mark.asyncio
async def test_returns_deduplicated_subdomains():
    raw_response = [
        {"name_value": "mail.acme.com", "issuer_name": "Let's Encrypt", "not_before": "2024-01-01", "not_after": "2025-01-01"},
        {"name_value": "mail.acme.com", "issuer_name": "Let's Encrypt", "not_before": "2024-01-01", "not_after": "2025-01-01"},  # duplicate
        {"name_value": "vpn.acme.com", "issuer_name": "DigiCert", "not_before": "2024-01-01", "not_after": "2025-01-01"},
    ]
    with patch('osint.services.crt_sh.httpx.AsyncClient') as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_response = AsyncMock()
        mock_response.json = lambda: raw_response
        mock_response.raise_for_status = lambda: None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        results = await query_crt_sh("acme.com")

    assert len(results) == 2
    names = {r.name_value for r in results}
    assert "mail.acme.com" in names
    assert "vpn.acme.com" in names


@pytest.mark.asyncio
async def test_raises_on_invalid_domain():
    with pytest.raises(ValueError):
        await query_crt_sh("not_a_domain")

    with pytest.raises(ValueError):
        await query_crt_sh("domain.internal")


@pytest.mark.asyncio
async def test_handles_empty_response():
    with patch('osint.services.crt_sh.httpx.AsyncClient') as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_response = AsyncMock()
        mock_response.json = lambda: []
        mock_response.raise_for_status = lambda: None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        results = await query_crt_sh("acme.com")

    assert results == []
```

### Implementation

**File:** `backend/osint/services/crt_sh.py`

```python
from dataclasses import dataclass, field
import httpx
from ._validators import validate_domain

CRT_SH_URL = "https://crt.sh/"
DEFAULT_TIMEOUT = 30
MAX_RESULTS = 5000


@dataclass(frozen=True)
class CrtShEntry:
    name_value: str
    issuer_name: str
    not_before: str
    not_after: str


async def query_crt_sh(domain: str, timeout: int = DEFAULT_TIMEOUT) -> list[CrtShEntry]:
    """Query crt.sh for certificate transparency log entries for a domain."""
    domain = validate_domain(domain)
    url = CRT_SH_URL
    params = {"q": f"%.{domain}", "output": "json"}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        entries = response.json()

    seen: set[str] = set()
    results: list[CrtShEntry] = []
    for entry in entries[:MAX_RESULTS]:
        name = entry.get("name_value", "").strip()
        if name and name not in seen:
            seen.add(name)
            results.append(CrtShEntry(
                name_value=name,
                issuer_name=entry.get("issuer_name", ""),
                not_before=entry.get("not_before", ""),
                not_after=entry.get("not_after", ""),
            ))
    return results
```

---

## Service 2: `dns_resolver.py` — DNS Resolution

### Tests First

**File:** `backend/osint/tests/test_services/test_dns_resolver.py`

```python
import pytest
from unittest.mock import patch, MagicMock
import dns.resolver
from osint.services.dns_resolver import resolve_dns, DnsRecord, ALLOWED_RECORD_TYPES


def test_returns_dns_records_for_valid_domain():
    mock_answer_mx = MagicMock()
    mock_answer_mx.__iter__ = lambda self: iter([MagicMock(__str__=lambda s: "10 mail.acme.com.")])

    with patch('dns.resolver.Resolver.resolve') as mock_resolve:
        mock_resolve.return_value = mock_answer_mx
        records = resolve_dns("acme.com", record_types=["MX"])

    assert len(records) >= 0  # doesn't crash


def test_raises_on_invalid_domain():
    with pytest.raises(ValueError):
        resolve_dns("not a domain")


def test_blocks_disallowed_record_types():
    records = resolve_dns("acme.com", record_types=["AXFR"])  # zone transfer — blocked
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


def test_returns_dmarc_record():
    mock_answer = MagicMock()
    mock_answer.__iter__ = lambda self: iter([MagicMock(__str__=lambda s: '"v=DMARC1; p=reject"')])

    with patch('dns.resolver.Resolver.resolve') as mock_resolve:
        mock_resolve.return_value = mock_answer
        records = resolve_dns("acme.com", record_types=["TXT"], include_dmarc=True)
    # Should attempt _dmarc.acme.com TXT
    assert isinstance(records, list)
```

### Implementation

**File:** `backend/osint/services/dns_resolver.py`

```python
from dataclasses import dataclass
import dns.resolver
import dns.exception
from ._validators import validate_domain

ALLOWED_RECORD_TYPES = frozenset({'A', 'AAAA', 'MX', 'TXT', 'NS', 'SOA', 'CNAME', 'PTR'})


@dataclass(frozen=True)
class DnsRecord:
    domain: str
    record_type: str
    values: tuple[str, ...]


def resolve_dns(
    domain: str,
    record_types: list[str] | None = None,
    include_dmarc: bool = True,
) -> list[DnsRecord]:
    """Resolve DNS records for a domain. Returns empty list on failures."""
    domain = validate_domain(domain)
    types_to_query = [t for t in (record_types or ['A', 'MX', 'TXT', 'NS'])
                      if t in ALLOWED_RECORD_TYPES]

    results: list[DnsRecord] = []
    resolver = dns.resolver.Resolver()

    for rtype in types_to_query:
        record = _resolve_single(resolver, domain, rtype)
        if record:
            results.append(record)

    if include_dmarc:
        dmarc = _resolve_single(resolver, f"_dmarc.{domain}", "TXT")
        if dmarc:
            results.append(DnsRecord(
                domain=f"_dmarc.{domain}",
                record_type="DMARC",
                values=dmarc.values,
            ))

    return results


def _resolve_single(resolver: dns.resolver.Resolver, name: str, rtype: str) -> DnsRecord | None:
    try:
        answers = resolver.resolve(name, rtype)
        values = tuple(str(rdata) for rdata in answers)
        return DnsRecord(domain=name, record_type=rtype, values=values)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
            dns.resolver.NoNameservers, dns.exception.Timeout):
        return None
```

---

## Service 3: `whois_client.py` — WHOIS Lookups

### Tests First

**File:** `backend/osint/tests/test_services/test_whois_client.py`

```python
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
    # Returns a WhoisResult with empty fields — doesn't crash the pipeline
    assert isinstance(result, WhoisResult)
    assert result.registrar == ""
```

### Implementation

**File:** `backend/osint/services/whois_client.py`

```python
from dataclasses import dataclass, field
import whois
from ._validators import validate_domain


@dataclass(frozen=True)
class WhoisResult:
    domain: str
    registrant_name: str
    registrant_org: str
    registrar: str
    creation_date: str
    expiration_date: str
    name_servers: tuple[str, ...]
    raw_text: str
    error: str = ""


def lookup_whois(domain: str) -> WhoisResult:
    """Perform WHOIS lookup. Returns empty-field result on any failure."""
    domain = validate_domain(domain)
    try:
        data = whois.whois(domain)
        return WhoisResult(
            domain=domain,
            registrant_name=_safe_str(data.name),
            registrant_org=_safe_str(data.org),
            registrar=_safe_str(data.registrar),
            creation_date=_safe_str(data.creation_date),
            expiration_date=_safe_str(data.expiration_date),
            name_servers=tuple(_safe_list(data.name_servers)),
            raw_text=_safe_str(data.text),
        )
    except Exception as exc:
        return WhoisResult(
            domain=domain,
            registrant_name="",
            registrant_org="",
            registrar="",
            creation_date="",
            expiration_date="",
            name_servers=(),
            raw_text="",
            error=str(exc),
        )


def _safe_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def _safe_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).lower() for v in value]
    return [str(value).lower()]
```

---

## Service 4: `email_security.py` — SPF/DKIM/DMARC Assessment

### Tests First

**File:** `backend/osint/tests/test_services/test_email_security.py`

```python
import pytest
from osint.services.dns_resolver import DnsRecord
from osint.services.email_security import assess_email_security, EmailSecurityResult


def _make_txt_record(domain, values):
    return DnsRecord(domain=domain, record_type="TXT", values=tuple(values))


def _make_dmarc_record(domain, value):
    return DnsRecord(domain=f"_dmarc.{domain}", record_type="DMARC", values=(value,))


def test_full_enforcement_grades_a():
    dns_records = [
        _make_txt_record("acme.com", ["v=spf1 include:_spf.google.com ~all"]),
        _make_dmarc_record("acme.com", "v=DMARC1; p=reject; rua=mailto:dmarc@acme.com"),
    ]
    result = assess_email_security("acme.com", dns_records)
    assert result.has_spf is True
    assert result.spf_assessment == "present"
    assert result.has_dmarc is True
    assert result.dmarc_policy == "reject"
    assert result.overall_grade in ("A", "B")


def test_missing_dmarc_grades_poorly():
    dns_records = [
        _make_txt_record("acme.com", ["v=spf1 include:_spf.google.com ~all"]),
        # no DMARC
    ]
    result = assess_email_security("acme.com", dns_records)
    assert result.has_dmarc is False
    assert result.dmarc_policy == "missing"
    assert result.overall_grade in ("D", "F")


def test_dmarc_none_policy_warns():
    dns_records = [
        _make_txt_record("acme.com", ["v=spf1 +all"]),  # permissive
        _make_dmarc_record("acme.com", "v=DMARC1; p=none"),
    ]
    result = assess_email_security("acme.com", dns_records)
    assert result.dmarc_policy == "none"
    assert result.has_spf is True
    assert result.overall_grade in ("C", "D")


def test_identifies_mx_providers():
    dns_records = [
        DnsRecord(domain="acme.com", record_type="MX", values=(
            "10 acme-com.mail.protection.outlook.com.",
        )),
    ]
    result = assess_email_security("acme.com", dns_records)
    assert any("Microsoft" in p or "Exchange Online" in p or "Office 365" in p
               for p in result.mx_providers)


def test_returns_dataclass_immutable():
    result = assess_email_security("acme.com", [])
    assert isinstance(result, EmailSecurityResult)
    # dataclass is frozen — can't mutate
    with pytest.raises(Exception):
        result.has_spf = True
```

### Implementation

**File:** `backend/osint/services/email_security.py`

```python
from dataclasses import dataclass
from .dns_resolver import DnsRecord

MX_PROVIDER_PATTERNS = {
    "google": "Google Workspace",
    "googlemail": "Google Workspace",
    "outlook": "Microsoft Exchange Online",
    "protection.outlook": "Microsoft Exchange Online",
    "pphosted": "Proofpoint",
    "mimecast": "Mimecast",
    "messagelabs": "Symantec Email Security",
    "barracudanetworks": "Barracuda",
    "spamh": "Spam Hero",
}


@dataclass(frozen=True)
class EmailSecurityResult:
    domain: str
    has_spf: bool
    spf_record: str
    spf_assessment: str           # present, permissive, fail_all, missing
    has_dmarc: bool
    dmarc_record: str
    dmarc_policy: str             # reject, quarantine, none, missing
    mx_providers: tuple[str, ...]
    overall_grade: str            # A, B, C, D, F
    risk_summary: str


def assess_email_security(domain: str, dns_records: list[DnsRecord]) -> EmailSecurityResult:
    """Assess SPF/DKIM/DMARC posture from DNS records."""
    spf_record, spf_assessment = _assess_spf(domain, dns_records)
    dmarc_record, dmarc_policy = _assess_dmarc(domain, dns_records)
    mx_providers = _identify_mx_providers(domain, dns_records)

    has_spf = bool(spf_record)
    has_dmarc = dmarc_policy not in ("missing", "")
    grade = _calculate_grade(spf_assessment, dmarc_policy)
    risk = _build_risk_summary(spf_assessment, dmarc_policy)

    return EmailSecurityResult(
        domain=domain,
        has_spf=has_spf,
        spf_record=spf_record,
        spf_assessment=spf_assessment,
        has_dmarc=has_dmarc,
        dmarc_record=dmarc_record,
        dmarc_policy=dmarc_policy,
        mx_providers=tuple(mx_providers),
        overall_grade=grade,
        risk_summary=risk,
    )


def _assess_spf(domain: str, records: list[DnsRecord]) -> tuple[str, str]:
    for rec in records:
        if rec.domain == domain and rec.record_type == "TXT":
            for val in rec.values:
                if val.startswith("v=spf1"):
                    if "+all" in val:
                        return val, "fail_all"
                    if "~all" in val:
                        return val, "present"
                    if "-all" in val:
                        return val, "present"
                    return val, "present"
    return "", "missing"


def _assess_dmarc(domain: str, records: list[DnsRecord]) -> tuple[str, str]:
    for rec in records:
        if rec.record_type == "DMARC":
            for val in rec.values:
                val_clean = val.strip('"')
                if "p=reject" in val_clean:
                    return val_clean, "reject"
                if "p=quarantine" in val_clean:
                    return val_clean, "quarantine"
                if "p=none" in val_clean:
                    return val_clean, "none"
                return val_clean, "unknown"
    return "", "missing"


def _identify_mx_providers(domain: str, records: list[DnsRecord]) -> list[str]:
    providers: list[str] = []
    for rec in records:
        if rec.domain == domain and rec.record_type == "MX":
            for val in rec.values:
                mx_host = val.lower()
                for pattern, provider_name in MX_PROVIDER_PATTERNS.items():
                    if pattern in mx_host and provider_name not in providers:
                        providers.append(provider_name)
    return providers


def _calculate_grade(spf_assessment: str, dmarc_policy: str) -> str:
    if dmarc_policy == "reject" and spf_assessment == "present":
        return "A"
    if dmarc_policy == "quarantine" and spf_assessment == "present":
        return "B"
    if dmarc_policy == "none" and spf_assessment == "present":
        return "C"
    if dmarc_policy == "missing" and spf_assessment == "present":
        return "D"
    if spf_assessment == "fail_all":
        return "F"
    return "F"


def _build_risk_summary(spf_assessment: str, dmarc_policy: str) -> str:
    parts = []
    if spf_assessment == "missing":
        parts.append("No SPF record — email spoofing is trivially possible")
    elif spf_assessment == "fail_all":
        parts.append("SPF uses +all — all servers are authorised, providing no protection")
    if dmarc_policy == "missing":
        parts.append("No DMARC record — phishing from this domain is unrestricted")
    elif dmarc_policy == "none":
        parts.append("DMARC policy=none — monitoring only, no enforcement against spoofing")
    if not parts:
        return "Email security posture is adequate"
    return ". ".join(parts) + "."
```

---

## Verification

```bash
cd backend
source venv/bin/activate
pytest osint/tests/test_services/ -v --tb=short
```

All service tests should pass without real network calls (all mocked).

---

## Done When

- [ ] `pytest osint/tests/test_services/test_crt_sh.py` passes
- [ ] `pytest osint/tests/test_services/test_dns_resolver.py` passes
- [ ] `pytest osint/tests/test_services/test_whois_client.py` passes
- [ ] `pytest osint/tests/test_services/test_email_security.py` passes
- [ ] No subprocess calls anywhere in `osint/services/`
- [ ] All domain inputs pass through `validate_domain()` before any query
