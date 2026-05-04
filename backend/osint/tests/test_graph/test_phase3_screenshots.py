import pytest
from unittest.mock import patch
from osint.graph.nodes.phase3_screenshots import phase3_analyze_screenshots


def _base_state(job_id: str) -> dict:
    return {
        "job_id": job_id,
        "organization_name": "Acme Corp",
        "primary_domain": "acme.com",
        "additional_domains": [],
        "engagement_context": "",
        "status": "phase3_processing",
        "error": "",
        "warnings": [],
        "screenshots": [],
        "screenshot_analyses": None,
        "research_job_id": None, "prior_research_context": None, "web_research": None,
        "breach_history": None, "job_postings_intel": None, "regulatory_framework": None,
        "vendor_relationships": None, "leadership_intel": None, "crt_sh_subdomains": None,
        "dns_records": None, "email_security": None, "whois_data": None, "arin_data": None,
        "terminal_submissions": None, "infrastructure_map": None, "technology_stack": None,
        "risk_matrix": None, "severity_table": None, "report_sections": None,
        "service_mappings": None, "report_file_path": None,
    }


@pytest.mark.django_db
def test_phase3_skips_gracefully_with_no_screenshots(osint_job):
    state = _base_state(str(osint_job.id))
    state['screenshots'] = []

    result = phase3_analyze_screenshots(state)

    assert result['status'] == 'phase4_analysis'
    assert result['screenshot_analyses'] == []
    osint_job.refresh_from_db()
    assert osint_job.status == 'phase4_analysis'


@pytest.mark.django_db
def test_phase3_processes_screenshots(osint_job):
    from osint.models import ScreenshotUpload
    import io
    from PIL import Image as PilImage
    from django.core.files.uploadedfile import InMemoryUploadedFile

    img = PilImage.new("RGB", (10, 10))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    screenshot = ScreenshotUpload.objects.create(
        osint_job=osint_job,
        source='dnsdumpster',
        image=InMemoryUploadedFile(buf, 'image', 'test.png', 'image/png', buf.getbuffer().nbytes, None),
    )

    state = _base_state(str(osint_job.id))
    state['screenshots'] = [str(screenshot.id)]

    mock_analysis = {
        "hosts_and_ips": ["1.2.3.4"],
        "open_ports": [443],
        "technology_indicators": ["nginx"],
        "security_observations": [],
        "infrastructure_providers": ["Cloudflare"],
        "notable_findings": [],
    }

    with patch('osint.graph.nodes.phase3_screenshots._analyze_all_screenshots',
               return_value=[mock_analysis]):
        result = phase3_analyze_screenshots(state)

    assert result['status'] == 'phase4_analysis'
    assert result['screenshot_analyses'] is not None
    assert len(result['screenshot_analyses']) == 1
