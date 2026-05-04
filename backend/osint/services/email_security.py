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
}


@dataclass(frozen=True)
class EmailSecurityResult:
    domain: str
    has_spf: bool
    spf_record: str
    spf_assessment: str
    has_dmarc: bool
    dmarc_record: str
    dmarc_policy: str
    mx_providers: tuple[str, ...]
    overall_grade: str
    risk_summary: str


def assess_email_security(domain: str, dns_records: list[DnsRecord]) -> EmailSecurityResult:
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
                if val.strip('"').startswith("v=spf1"):
                    clean = val.strip('"')
                    if "+all" in clean:
                        return clean, "fail_all"
                    return clean, "present"
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
