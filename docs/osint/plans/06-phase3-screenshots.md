# Plan 06 — Phase 3: Screenshot Upload & Gemini Vision Analysis

**Depends on:** Plans 01, 03, 05  
**Unlocks:** Plan 07 (Phase 4 analysis + report)

---

## Goal

Implement screenshot upload (multipart POST), Gemini vision analysis of each image, and the Phase 3 LangGraph node that resumes the workflow after the second human-in-the-loop interrupt.

---

## The Human Gate

The workflow sits at `interrupt_before=['phase3_screenshots']`. The graph is frozen waiting for the user to upload screenshots. The `submit-screenshots` endpoint resumes it by calling:

```python
graph.invoke(
    {"screenshots": [...]},  # list of screenshot metadata dicts
    config={"configurable": {"thread_id": str(job_id)}},
)
```

---

## TDD

### Screenshot Upload View Tests

**File:** `backend/osint/tests/test_views/test_screenshots.py`

```python
import io
import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from PIL import Image as PilImage
from osint.models import OsintJob, ScreenshotUpload


@pytest.fixture
def api():
    return APIClient()


def _make_png_file(name="test.png") -> tuple:
    """Create an in-memory PNG file for upload testing."""
    img = PilImage.new("RGB", (100, 100), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return name, buf, "image/png"


@pytest.mark.django_db
def test_upload_screenshots_accepts_valid_image(api, osint_job):
    osint_job.status = 'awaiting_screenshots'
    osint_job.save()

    name, buf, mime = _make_png_file()

    with patch('osint.views.SubmitScreenshotsView._resume_graph'):
        url = reverse('osint-submit-screenshots', kwargs={'pk': osint_job.id})
        response = api.post(
            url,
            data={'source': 'dnsdumpster', 'image': (buf, name, mime)},
            format='multipart',
        )

    assert response.status_code == 202
    assert ScreenshotUpload.objects.filter(osint_job=osint_job).count() == 1


@pytest.mark.django_db
def test_upload_rejects_wrong_status(api, osint_job):
    osint_job.status = 'phase4_analysis'
    osint_job.save()

    name, buf, mime = _make_png_file()
    url = reverse('osint-submit-screenshots', kwargs={'pk': osint_job.id})
    response = api.post(
        url,
        data={'source': 'dnsdumpster', 'image': (buf, name, mime)},
        format='multipart',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_rejects_non_image_file(api, osint_job):
    osint_job.status = 'awaiting_screenshots'
    osint_job.save()

    buf = io.BytesIO(b"This is not an image, it is a text file.")
    buf.seek(0)

    url = reverse('osint-submit-screenshots', kwargs={'pk': osint_job.id})
    response = api.post(
        url,
        data={'source': 'dnsdumpster', 'image': (buf, 'notanimage.txt', 'text/plain')},
        format='multipart',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_rejects_too_many_files(api, osint_job):
    osint_job.status = 'awaiting_screenshots'
    osint_job.save()

    # The view should enforce a max of 20 screenshots per job
    for i in range(20):
        img = PilImage.new("RGB", (10, 10))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        ScreenshotUpload.objects.create(
            osint_job=osint_job,
            source='dnsdumpster',
            image='fake_path.png',
        )

    name, buf, mime = _make_png_file()
    url = reverse('osint-submit-screenshots', kwargs={'pk': osint_job.id})
    response = api.post(
        url,
        data={'source': 'dnsdumpster', 'image': (buf, name, mime)},
        format='multipart',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_validates_source_field(api, osint_job):
    osint_job.status = 'awaiting_screenshots'
    osint_job.save()

    name, buf, mime = _make_png_file()
    url = reverse('osint-submit-screenshots', kwargs={'pk': osint_job.id})
    response = api.post(
        url,
        data={'source': 'INVALID_SOURCE', 'image': (buf, name, mime)},
        format='multipart',
    )
    assert response.status_code == 400
```

### Screenshot Analyzer Service Tests

**File:** `backend/osint/tests/test_services/test_screenshot_analyzer.py`

```python
import io
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image as PilImage
from osint.services.screenshot_analyzer import analyze_screenshot, ScreenshotAnalysis


def _make_test_image_bytes() -> bytes:
    img = PilImage.new("RGB", (800, 600), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_returns_structured_analysis():
    image_bytes = _make_test_image_bytes()
    mock_gemini_response = {
        "hosts_and_ips": ["192.168.1.1", "mail.acme.com"],
        "open_ports": [80, 443, 22],
        "technology_indicators": ["Apache 2.4", "Ubuntu Linux"],
        "security_observations": ["Port 22 (SSH) exposed to internet"],
        "infrastructure_providers": ["AWS us-east-1"],
        "notable_findings": ["Unpatched SSH banner detected"],
    }

    with patch('osint.services.screenshot_analyzer._call_gemini_vision',
               return_value=mock_gemini_response):
        result = analyze_screenshot(image_bytes, source='shodan', domain='acme.com')

    assert isinstance(result, ScreenshotAnalysis)
    assert "192.168.1.1" in result.hosts_and_ips
    assert "Apache 2.4" in result.technology_indicators


def test_handles_gemini_failure_gracefully():
    image_bytes = _make_test_image_bytes()

    with patch('osint.services.screenshot_analyzer._call_gemini_vision',
               side_effect=Exception("Gemini API error")):
        result = analyze_screenshot(image_bytes, source='dnsdumpster', domain='acme.com')

    assert isinstance(result, ScreenshotAnalysis)
    assert result.error != ""
    assert result.hosts_and_ips == ()  # empty, not crashed


def test_validates_image_bytes_are_image():
    not_an_image = b"this is plain text not an image"
    with pytest.raises(ValueError, match="not a valid image"):
        analyze_screenshot(not_an_image, source='dnsdumpster', domain='acme.com')


def test_returns_immutable_dataclass():
    image_bytes = _make_test_image_bytes()
    with patch('osint.services.screenshot_analyzer._call_gemini_vision',
               return_value={"hosts_and_ips": [], "open_ports": [], "technology_indicators": [],
                             "security_observations": [], "infrastructure_providers": [],
                             "notable_findings": []}):
        result = analyze_screenshot(image_bytes, source='shodan', domain='acme.com')

    with pytest.raises(Exception):  # frozen dataclass
        result.hosts_and_ips = ["new.host"]
```

### Phase 3 Node Tests

**File:** `backend/osint/tests/test_graph/test_phase3_screenshots.py`

```python
import pytest
from unittest.mock import patch
from osint.graph.nodes.phase3_screenshots import phase3_analyze_screenshots


@pytest.mark.django_db
def test_phase3_processes_uploaded_screenshots(osint_job):
    state = {
        "job_id": str(osint_job.id),
        "organization_name": "Acme Corp",
        "primary_domain": "acme.com",
        "screenshots": [str(osint_job.id)],  # list of ScreenshotUpload IDs
        "status": "phase3_processing",
        "error": "",
        "warnings": [],
        **{k: None for k in ["additional_domains", "engagement_context", "research_job_id",
                              "prior_research_context", "web_research", "breach_history",
                              "job_postings_intel", "regulatory_framework", "vendor_relationships",
                              "leadership_intel", "crt_sh_subdomains", "dns_records",
                              "email_security", "whois_data", "arin_data", "terminal_submissions",
                              "screenshot_analyses", "infrastructure_map", "technology_stack",
                              "risk_matrix", "severity_table", "report_sections",
                              "service_mappings", "report_file_path"]},
    }

    with patch('osint.graph.nodes.phase3_screenshots._analyze_all_screenshots',
               return_value=[{"hosts_and_ips": ["1.2.3.4"], "technology_indicators": ["nginx"]}]):
        result = phase3_analyze_screenshots(state)

    assert result['status'] == 'phase4_analysis'
    assert result['screenshot_analyses'] is not None


@pytest.mark.django_db
def test_phase3_skips_gracefully_with_no_screenshots(osint_job):
    state = {
        "job_id": str(osint_job.id),
        "organization_name": "Acme Corp",
        "primary_domain": "acme.com",
        "screenshots": [],  # empty — user skipped Phase 3
        "status": "phase3_processing",
        "error": "",
        "warnings": [],
        **{k: None for k in ["additional_domains", "engagement_context", "research_job_id",
                              "prior_research_context", "web_research", "breach_history",
                              "job_postings_intel", "regulatory_framework", "vendor_relationships",
                              "leadership_intel", "crt_sh_subdomains", "dns_records",
                              "email_security", "whois_data", "arin_data", "terminal_submissions",
                              "screenshot_analyses", "infrastructure_map", "technology_stack",
                              "risk_matrix", "severity_table", "report_sections",
                              "service_mappings", "report_file_path"]},
    }

    result = phase3_analyze_screenshots(state)

    assert result['status'] == 'phase4_analysis'
    assert result['screenshot_analyses'] == []
```

---

## Implementations

### `screenshot_analyzer.py`

**File:** `backend/osint/services/screenshot_analyzer.py`

```python
import io
import json
from dataclasses import dataclass, field
from django.conf import settings
from PIL import Image as PilImage

VISION_PROMPT = """You are a cybersecurity analyst examining a screenshot from {source} for the domain {domain}.

Extract all observable intelligence from this image:
1. IP addresses and hostnames visible
2. Open ports and running services
3. Technology stack indicators (web servers, OS, frameworks, certificates)
4. Infrastructure providers (cloud, CDN, hosting)
5. Security observations (exposed services, misconfigurations, certificate details)
6. Any notable findings (unusual ports, old software versions, shared IPs)

Return ONLY valid JSON:
{{
    "hosts_and_ips": ["string"],
    "open_ports": [integer],
    "technology_indicators": ["string"],
    "security_observations": ["string"],
    "infrastructure_providers": ["string"],
    "notable_findings": ["string"]
}}"""


@dataclass(frozen=True)
class ScreenshotAnalysis:
    source: str
    domain: str
    hosts_and_ips: tuple[str, ...]
    open_ports: tuple[int, ...]
    technology_indicators: tuple[str, ...]
    security_observations: tuple[str, ...]
    infrastructure_providers: tuple[str, ...]
    notable_findings: tuple[str, ...]
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
            open_ports=tuple(int(p) for p in raw.get("open_ports", []) if str(p).isdigit()),
            technology_indicators=tuple(raw.get("technology_indicators", [])),
            security_observations=tuple(raw.get("security_observations", [])),
            infrastructure_providers=tuple(raw.get("infrastructure_providers", [])),
            notable_findings=tuple(raw.get("notable_findings", [])),
        )
    except Exception as exc:
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
        text = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

    return json.loads(text)
```

### `SubmitScreenshotsView`

**Update `backend/osint/views.py`:**

```python
from django.core.files.uploadedfile import InMemoryUploadedFile
from osint.models import ScreenshotUpload

VALID_SOURCES = {'dnsdumpster', 'shodan', 'other'}
MAX_SCREENSHOTS = 20
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class SubmitScreenshotsView(APIView):
    def post(self, request, pk):
        try:
            job = OsintJob.objects.select_for_update().get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'awaiting_screenshots':
            return Response(
                {'detail': f'Expected awaiting_screenshots, got {job.status}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # Validate source field
        source = request.data.get('source', '')
        if source not in VALID_SOURCES:
            return Response(
                {'detail': f'source must be one of: {", ".join(VALID_SOURCES)}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # Check screenshot count limit
        existing_count = ScreenshotUpload.objects.filter(osint_job=job).count()
        if existing_count >= MAX_SCREENSHOTS:
            return Response(
                {'detail': f'Maximum {MAX_SCREENSHOTS} screenshots per job'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # Validate and save uploaded file
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'detail': 'image file required'}, status=http_status.HTTP_400_BAD_REQUEST)

        if image_file.size > MAX_FILE_SIZE:
            return Response(
                {'detail': f'File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # Validate it's actually an image using Pillow
        try:
            from PIL import Image as PilImage
            import io
            image_bytes = image_file.read()
            buf = io.BytesIO(image_bytes)
            img = PilImage.open(buf)
            img.verify()
            image_file.seek(0)  # reset after read
        except Exception:
            return Response(
                {'detail': 'Uploaded file is not a valid image (PNG, JPEG, or WebP required)'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        caption = request.data.get('caption', '')
        screenshot = ScreenshotUpload.objects.create(
            osint_job=job,
            source=source,
            image=image_file,
            caption=caption,
        )

        # Transition job and resume graph
        job.status = 'phase3_processing'
        job.save(update_fields=['status', 'updated_at'])

        screenshot_ids = list(
            ScreenshotUpload.objects.filter(osint_job=job).values_list('id', flat=True)
        )

        import threading
        t = threading.Thread(
            target=self._resume_graph,
            args=(str(job.id), [str(sid) for sid in screenshot_ids]),
            daemon=True,
        )
        t.start()

        return Response(
            {'detail': 'Screenshot uploaded, analysis resuming.', 'screenshot_id': str(screenshot.id)},
            status=http_status.HTTP_202_ACCEPTED,
        )

    def _resume_graph(self, job_id: str, screenshot_ids: list) -> None:
        from osint.graph.workflow import get_graph
        graph = get_graph()
        config = {"configurable": {"thread_id": job_id}}
        graph.invoke(
            {"screenshots": screenshot_ids},
            config=config,
        )
```

### `phase3_screenshots.py` node

**File:** `backend/osint/graph/nodes/phase3_screenshots.py`

```python
from osint.graph.state import OsintState
from osint.models import OsintJob, ScreenshotUpload


def phase3_analyze_screenshots(state: OsintState) -> OsintState:
    """Phase 3: Analyze user-uploaded screenshots via Gemini vision."""
    screenshot_ids = state.get('screenshots') or []

    if not screenshot_ids:
        OsintJob.objects.filter(pk=state['job_id']).update(status='phase4_analysis')
        return {
            **state,
            'status': 'phase4_analysis',
            'screenshot_analyses': [],
        }

    try:
        analyses = _analyze_all_screenshots(screenshot_ids, state['primary_domain'])
        _save_analyses_to_db(screenshot_ids, analyses)
        OsintJob.objects.filter(pk=state['job_id']).update(status='phase4_analysis')

        return {
            **state,
            'status': 'phase4_analysis',
            'screenshot_analyses': analyses,
        }
    except Exception as exc:
        OsintJob.objects.filter(pk=state['job_id']).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}


def _analyze_all_screenshots(screenshot_ids: list[str], domain: str) -> list[dict]:
    from osint.services.screenshot_analyzer import analyze_screenshot

    analyses = []
    for sid in screenshot_ids:
        try:
            screenshot = ScreenshotUpload.objects.get(pk=sid)
            image_bytes = screenshot.image.read()
            result = analyze_screenshot(image_bytes, source=screenshot.source, domain=domain)
            analyses.append({
                'screenshot_id': sid,
                'source': screenshot.source,
                'hosts_and_ips': list(result.hosts_and_ips),
                'technology_indicators': list(result.technology_indicators),
                'security_observations': list(result.security_observations),
                'infrastructure_providers': list(result.infrastructure_providers),
                'notable_findings': list(result.notable_findings),
                'error': result.error,
            })
        except Exception as exc:
            analyses.append({'screenshot_id': sid, 'error': str(exc)})
    return analyses


def _save_analyses_to_db(screenshot_ids: list[str], analyses: list[dict]) -> None:
    for analysis in analyses:
        sid = analysis.get('screenshot_id')
        if sid:
            ScreenshotUpload.objects.filter(pk=sid).update(
                analysis=str(analysis),
                extracted_data={k: v for k, v in analysis.items() if k != 'screenshot_id'},
            )
```

---

## Verification

```bash
cd backend
source venv/bin/activate
pytest osint/tests/test_views/test_screenshots.py -v
pytest osint/tests/test_services/test_screenshot_analyzer.py -v
pytest osint/tests/test_graph/test_phase3_screenshots.py -v

# Manual upload test:
# Create job, execute, submit terminal output, then:
curl -X POST http://localhost:8000/api/osint/jobs/{id}/submit-screenshots/ \
  -F "source=dnsdumpster" \
  -F "caption=DNSDumpster map for acme.com" \
  -F "image=@/path/to/screenshot.png"
```

---

## Done When

- [ ] Upload accepts PNG/JPEG/WebP, rejects non-images
- [ ] Upload rejects files > 10MB
- [ ] Upload rejects when job status is not `awaiting_screenshots`
- [ ] Upload enforces 20-file max per job
- [ ] Gemini vision analysis runs per screenshot and is saved to `ScreenshotUpload.extracted_data`
- [ ] Phase 3 skips gracefully with empty screenshots list
- [ ] Status transitions: `awaiting_screenshots → phase3_processing → phase4_analysis`
- [ ] All tests pass
