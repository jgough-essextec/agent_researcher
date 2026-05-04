import io
import pytest
from unittest.mock import patch
from PIL import Image as PilImage
from osint.services.screenshot_analyzer import analyze_screenshot, ScreenshotAnalysis


def _make_png_bytes() -> bytes:
    img = PilImage.new("RGB", (100, 100), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_returns_structured_analysis():
    image_bytes = _make_png_bytes()
    mock_response = {
        "hosts_and_ips": ["192.168.1.1", "mail.acme.com"],
        "open_ports": [80, 443],
        "technology_indicators": ["Apache 2.4"],
        "security_observations": ["Port 22 exposed"],
        "infrastructure_providers": ["AWS us-east-1"],
        "notable_findings": ["Unpatched SSH banner"],
    }
    with patch('osint.services.screenshot_analyzer._call_gemini_vision', return_value=mock_response):
        result = analyze_screenshot(image_bytes, source='shodan', domain='acme.com')

    assert isinstance(result, ScreenshotAnalysis)
    assert "192.168.1.1" in result.hosts_and_ips
    assert "Apache 2.4" in result.technology_indicators


def test_handles_gemini_failure_gracefully():
    image_bytes = _make_png_bytes()
    with patch('osint.services.screenshot_analyzer._call_gemini_vision',
               side_effect=Exception("Gemini API error")):
        result = analyze_screenshot(image_bytes, source='dnsdumpster', domain='acme.com')

    assert isinstance(result, ScreenshotAnalysis)
    assert result.error != ""
    assert result.hosts_and_ips == ()


def test_rejects_non_image_bytes():
    not_an_image = b"this is plain text not an image"
    with pytest.raises(ValueError, match="not a valid image"):
        analyze_screenshot(not_an_image, source='dnsdumpster', domain='acme.com')


def test_returns_immutable_frozen_dataclass():
    image_bytes = _make_png_bytes()
    with patch('osint.services.screenshot_analyzer._call_gemini_vision',
               return_value={"hosts_and_ips": [], "open_ports": [], "technology_indicators": [],
                             "security_observations": [], "infrastructure_providers": [],
                             "notable_findings": []}):
        result = analyze_screenshot(image_bytes, source='shodan', domain='acme.com')

    with pytest.raises(Exception):
        result.hosts_and_ips = ["new.host"]  # frozen dataclass
