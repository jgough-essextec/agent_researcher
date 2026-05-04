import io
import json
import logging
from dataclasses import dataclass

from django.conf import settings
from PIL import Image as PilImage

logger = logging.getLogger(__name__)

VISION_PROMPT = """You are a cybersecurity analyst examining a screenshot from {source} for the domain {domain}.

Extract all observable intelligence from this image:
1. IP addresses and hostnames visible
2. Open ports and running services
3. Technology stack indicators (web servers, OS, frameworks, certificates)
4. Infrastructure providers (cloud, CDN, hosting)
5. Security observations (exposed services, misconfigurations, certificate details)
6. Any notable findings (unusual ports, old software versions, shared IPs)

Return ONLY valid JSON with no markdown fencing:
{{
    "hosts_and_ips": ["string"],
    "open_ports": [0],
    "technology_indicators": ["string"],
    "security_observations": ["string"],
    "infrastructure_providers": ["string"],
    "notable_findings": ["string"]
}}"""


@dataclass(frozen=True)
class ScreenshotAnalysis:
    source: str
    domain: str
    hosts_and_ips: tuple
    open_ports: tuple
    technology_indicators: tuple
    security_observations: tuple
    infrastructure_providers: tuple
    notable_findings: tuple
    error: str = ""


def analyze_screenshot(image_bytes: bytes, source: str, domain: str) -> ScreenshotAnalysis:
    """Analyze a screenshot using Gemini vision. Returns empty-field result on failure."""
    _validate_image(image_bytes)

    try:
        raw = _call_gemini_vision(image_bytes, source, domain)
        return ScreenshotAnalysis(
            source=source,
            domain=domain,
            hosts_and_ips=tuple(raw.get("hosts_and_ips", [])),
            open_ports=tuple(
                int(p) for p in raw.get("open_ports", [])
                if str(p).isdigit() or isinstance(p, int)
            ),
            technology_indicators=tuple(raw.get("technology_indicators", [])),
            security_observations=tuple(raw.get("security_observations", [])),
            infrastructure_providers=tuple(raw.get("infrastructure_providers", [])),
            notable_findings=tuple(raw.get("notable_findings", [])),
        )
    except Exception as exc:
        logger.warning("Gemini vision analysis failed: %s", exc)
        return ScreenshotAnalysis(
            source=source,
            domain=domain,
            hosts_and_ips=(),
            open_ports=(),
            technology_indicators=(),
            security_observations=(),
            infrastructure_providers=(),
            notable_findings=(),
            error=str(exc),
        )


def _validate_image(image_bytes: bytes) -> None:
    """Verify bytes represent a valid image using Pillow."""
    try:
        buf = io.BytesIO(image_bytes)
        img = PilImage.open(buf)
        img.verify()
    except Exception:
        raise ValueError("Provided bytes are not a valid image")


def _call_gemini_vision(image_bytes: bytes, source: str, domain: str) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = VISION_PROMPT.format(source=source, domain=domain)

    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
        ],
    )

    text = response.text.strip()
    if text.startswith("```"):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1] if lines and lines[-1].strip() == '```' else lines[1:])

    return json.loads(text)
