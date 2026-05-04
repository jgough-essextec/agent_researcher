import asyncio
from django.utils import timezone
from osint.graph.state import OsintState
from osint.models import OsintJob, DnsFinding, SubdomainFinding, EmailSecurityAssessment, WhoisRecord


def phase2_auto_dns(state: OsintState) -> OsintState:
    """Phase 2 automated: crt.sh, DNS, email security, WHOIS."""
    job_id = state['job_id']
    domain = state['primary_domain']

    try:
        subdomains = _collect_crt_sh(domain)
        dns_records = _collect_dns_records(domain)
        whois_data = _collect_whois(domain)
        email_assessment = _assess_email(domain, dns_records)

        _persist_findings(job_id, domain, subdomains, dns_records, whois_data, email_assessment)
        OsintJob.objects.filter(pk=job_id).update(
            status='phase2_auto',
            phase2_completed_at=timezone.now(),
        )

        return {
            **state,
            'status': 'phase2_auto',
            'crt_sh_subdomains': subdomains,
            'dns_records': dns_records,
            'whois_data': whois_data,
            'email_security': {
                'domain': email_assessment.domain,
                'has_spf': email_assessment.has_spf,
                'spf_assessment': email_assessment.spf_assessment,
                'has_dmarc': email_assessment.has_dmarc,
                'dmarc_policy': email_assessment.dmarc_policy,
                'overall_grade': email_assessment.overall_grade,
                'risk_summary': email_assessment.risk_summary,
                'mx_providers': list(email_assessment.mx_providers),
            },
            'error': '',
        }
    except Exception as exc:
        OsintJob.objects.filter(pk=job_id).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}


def _collect_crt_sh(domain: str) -> list[dict]:
    try:
        from osint.services.crt_sh import query_crt_sh
        entries = asyncio.run(query_crt_sh(domain))
        return [{"name_value": e.name_value, "issuer_name": e.issuer_name} for e in entries]
    except Exception:
        return []


def _collect_dns_records(domain: str) -> list[dict]:
    from osint.services.dns_resolver import resolve_dns
    records = resolve_dns(domain, record_types=['A', 'MX', 'TXT', 'NS', 'SOA'], include_dmarc=True)
    return [{"domain": r.domain, "record_type": r.record_type, "values": list(r.values)}
            for r in records]


def _collect_whois(domain: str) -> dict:
    from osint.services.whois_client import lookup_whois
    result = lookup_whois(domain)
    return {
        "registrant_org": result.registrant_org,
        "registrar": result.registrar,
        "creation_date": result.creation_date,
        "expiration_date": result.expiration_date,
        "name_servers": list(result.name_servers),
    }


def _assess_email(domain: str, dns_records_raw: list[dict]):
    from osint.services.dns_resolver import DnsRecord
    from osint.services.email_security import assess_email_security
    dns_records = [
        DnsRecord(domain=r['domain'], record_type=r['record_type'], values=tuple(r['values']))
        for r in dns_records_raw
    ]
    return assess_email_security(domain, dns_records)


def _persist_findings(
    job_id: str,
    domain: str,
    subdomains: list[dict],
    dns_records: list[dict],
    whois_data: dict,
    email_assessment,
) -> None:
    for record in dns_records:
        for val in record['values']:
            DnsFinding.objects.create(
                osint_job_id=job_id,
                domain=record['domain'],
                record_type=record['record_type'],
                record_value=val,
            )

    for sub in subdomains:
        SubdomainFinding.objects.get_or_create(
            osint_job_id=job_id,
            subdomain=sub['name_value'],
            defaults={'source': 'crt_sh'},
        )

    if whois_data and any(whois_data.values()):
        WhoisRecord.objects.create(
            osint_job_id=job_id,
            domain=domain,
            registrant_org=whois_data.get('registrant_org', ''),
            registrar=whois_data.get('registrar', ''),
            name_servers=whois_data.get('name_servers', []),
        )

    EmailSecurityAssessment.objects.create(
        osint_job_id=job_id,
        domain=domain,
        has_spf=email_assessment.has_spf,
        spf_record=email_assessment.spf_record,
        spf_assessment=email_assessment.spf_assessment,
        has_dmarc=email_assessment.has_dmarc,
        dmarc_record=email_assessment.dmarc_record,
        dmarc_policy=email_assessment.dmarc_policy,
        mx_providers=list(email_assessment.mx_providers),
        overall_grade=email_assessment.overall_grade,
        risk_summary=email_assessment.risk_summary,
    )
