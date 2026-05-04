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
    """Resolve DNS records for a domain using dnspython (no subprocess)."""
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
