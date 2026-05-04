from osint.graph.state import OsintState
from osint.models import OsintJob, OsintCommandRound


def generate_terminal_commands(state: OsintState) -> OsintState:
    """Generate personalised terminal commands for the user to run locally."""
    job_id = state['job_id']
    domain = state['primary_domain']
    subdomains = state.get('crt_sh_subdomains') or []
    dns_records = state.get('dns_records') or []

    commands = _build_round1_commands(domain, subdomains, dns_records)
    rationale = _build_rationale(domain, subdomains, dns_records)

    OsintCommandRound.objects.create(
        osint_job_id=job_id,
        round_number=1,
        commands=commands,
        rationale=rationale,
    )

    OsintJob.objects.filter(pk=job_id).update(status='awaiting_terminal_output')

    return {**state, 'status': 'awaiting_terminal_output'}


def _build_round1_commands(domain: str, subdomains: list, dns_records: list) -> list[str]:
    """Build Round 1 terminal commands. CRITICAL: No lines starting with #."""
    commands = []

    commands.append(
        f'curl -s "https://crt.sh/?q=%.{domain}&output=json" | '
        f'python3 -c "import sys,json; [print(e[\'name_value\']) for e in json.load(sys.stdin)]" | sort -u'
    )
    commands.append(f'whois {domain}')
    commands.append(f'dig {domain} MX TXT NS SOA +short')
    commands.append(f'dig _dmarc.{domain} TXT +short')
    commands.append(f'dig {domain} A +short')

    interesting = _filter_interesting_subdomains(subdomains)
    for sub in interesting[:10]:
        commands.append(f'dig {sub} A +short')

    spf_includes = _extract_spf_includes(dns_records)
    for include in spf_includes[:3]:
        commands.append(f'dig {include} TXT +short')

    return commands


def _build_rationale(domain: str, subdomains: list, dns_records: list) -> str:
    parts = [f"Run these commands for {domain}."]
    if subdomains:
        parts.append(
            f"We found {len(subdomains)} subdomains via certificate transparency — "
            "these commands verify which ones are actively resolving."
        )
    spf_includes = _extract_spf_includes(dns_records)
    if spf_includes:
        parts.append(
            f"SPF record references {len(spf_includes)} external providers — "
            "we will expand those to identify all authorised email senders."
        )
    parts.append("Paste the complete output below when done.")
    return " ".join(parts)


def _filter_interesting_subdomains(subdomains: list) -> list[str]:
    interesting_keywords = (
        'vpn', 'remote', 'access', 'portal', 'admin', 'stage', 'staging',
        'dev', 'test', 'uat', 'api', 'legacy', 'old', 'mail', 'smtp',
    )
    results = []
    seen: set[str] = set()
    for sub in subdomains:
        name = sub.get('name_value', '').lower()
        if any(kw in name for kw in interesting_keywords) and name not in seen:
            seen.add(name)
            results.append(sub.get('name_value', ''))
    return [r for r in results if r]


def _extract_spf_includes(dns_records: list) -> list[str]:
    includes = []
    for rec in dns_records:
        if rec.get('record_type') == 'TXT':
            for val in rec.get('values', []):
                if 'v=spf1' in val:
                    for part in val.split():
                        if part.startswith('include:'):
                            includes.append(part[8:])
    return includes
