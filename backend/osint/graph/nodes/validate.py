import re
from osint.graph.state import OsintState

_DOMAIN_RE = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?'
    r'(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*'
    r'\.[a-zA-Z]{2,}$'
)


def validate_osint_input(state: OsintState) -> OsintState:
    domain = state.get('primary_domain', '').strip().lower()
    org = state.get('organization_name', '').strip()

    if not org:
        return {**state, 'status': 'failed', 'error': 'organization_name is required'}
    if not domain or not _DOMAIN_RE.match(domain):
        return {**state, 'status': 'failed', 'error': f'Invalid primary_domain: {domain}'}

    return {**state, 'status': 'phase1_research', 'primary_domain': domain}
