from dataclasses import dataclass
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
    """Perform WHOIS lookup using python-whois (no subprocess)."""
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
        return [str(v).lower() for v in value if v]
    return [str(value).lower()]
