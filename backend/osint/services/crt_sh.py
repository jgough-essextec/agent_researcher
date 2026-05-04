from dataclasses import dataclass
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
    """Query crt.sh for certificate transparency log entries."""
    domain = validate_domain(domain)
    params = {"q": f"%.{domain}", "output": "json"}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(CRT_SH_URL, params=params)
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
