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
