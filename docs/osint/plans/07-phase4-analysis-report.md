# Plan 07 — Phase 4 Analysis, Phase 5 Report & .docx Builder

**Depends on:** Plans 01–06 (all backend plans)  
**Unlocks:** Plan 08 (frontend)

---

## Goal

Implement the final two automated phases:

1. **Phase 4** — Gemini synthesis of all findings: infrastructure map, technology stack, risk matrix (Likelihood × Impact), severity table, service mappings
2. **Phase 5** — Generate all 9 report sections via Gemini, persist to `OsintReportSection` model
3. **`OsintReportBuilder`** — python-docx builder that renders all sections into a professional `.docx` file
4. **Download endpoint** — `GET /api/osint/jobs/{id}/report/` returns the file

---

## New Dependency

Add to `backend/requirements.txt`:
```
python-docx>=1.1
```

Install: `pip install python-docx`

---

## TDD

### Risk Assessor Service Tests

**File:** `backend/osint/tests/test_services/test_risk_assessor.py`

```python
import pytest
from osint.services.risk_assessor import calculate_risk_score, classify_severity, RiskLevel


def test_high_likelihood_high_impact_is_critical():
    score = calculate_risk_score(likelihood=5, impact=5)
    assert score == 25
    assert classify_severity(score) == RiskLevel.CRITICAL


def test_low_likelihood_low_impact_is_low():
    score = calculate_risk_score(likelihood=1, impact=1)
    assert score == 1
    assert classify_severity(score) == RiskLevel.LOW


def test_medium_risk():
    score = calculate_risk_score(likelihood=3, impact=3)
    assert score == 9
    assert classify_severity(score) == RiskLevel.HIGH


def test_likelihood_impact_must_be_1_to_5():
    with pytest.raises(ValueError):
        calculate_risk_score(likelihood=0, impact=3)
    with pytest.raises(ValueError):
        calculate_risk_score(likelihood=3, impact=6)


def test_dmarc_none_is_high_risk():
    from osint.services.risk_assessor import assess_email_security_risk
    result = assess_email_security_risk(dmarc_policy="none", spf_assessment="present")
    assert result.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL)


def test_full_enforcement_is_low_risk():
    from osint.services.risk_assessor import assess_email_security_risk
    result = assess_email_security_risk(dmarc_policy="reject", spf_assessment="present")
    assert result.severity in (RiskLevel.LOW, RiskLevel.MEDIUM)
```

### Report Builder Tests

**File:** `backend/osint/tests/test_report/test_builder.py`

```python
import os
import pytest
from unittest.mock import MagicMock, patch
from osint.report.builder import OsintReportBuilder
from osint.models import OsintJob, OsintReportSection


@pytest.mark.django_db
def test_builder_creates_docx_file(osint_job, tmp_path):
    OsintReportSection.objects.create(
        osint_job=osint_job,
        section_type='cover',
        title='Cover',
        content='Confidential',
        order=0,
    )
    OsintReportSection.objects.create(
        osint_job=osint_job,
        section_type='executive_summary',
        title='Executive Summary',
        content='This organization has several security risks.',
        structured_data={'grade': 'C'},
        order=1,
    )

    with patch('osint.report.builder.settings') as mock_settings:
        mock_settings.MEDIA_ROOT = str(tmp_path)
        builder = OsintReportBuilder(osint_job)
        builder.add_all_sections()
        output_path = builder.build()

    assert os.path.exists(output_path)
    assert output_path.endswith('.docx')
    assert os.path.getsize(output_path) > 0


@pytest.mark.django_db
def test_builder_does_not_mutate_job(osint_job):
    original_status = osint_job.status
    builder = OsintReportBuilder(osint_job)
    builder.add_all_sections()
    # Don't call build() — just verify no side effects on job object
    osint_job.refresh_from_db()
    assert osint_job.status == original_status


@pytest.mark.django_db
def test_generate_report_endpoint_triggers_report_build(api_client, osint_job):
    osint_job.status = 'phase4_analysis'
    osint_job.phase4_completed_at = __import__('django.utils.timezone', fromlist=['timezone']).timezone.now()
    osint_job.save()

    with patch('osint.views.GenerateReportView._build_report_async'):
        from django.urls import reverse
        url = reverse('osint-generate-report', kwargs={'pk': osint_job.id})
        response = api_client.post(url)

    assert response.status_code == 202


@pytest.mark.django_db
def test_download_report_returns_file(api_client, osint_job, tmp_path):
    # Create a minimal .docx file
    from docx import Document
    doc = Document()
    doc.add_paragraph("Test report")
    file_path = tmp_path / "test_report.docx"
    doc.save(str(file_path))

    osint_job.status = 'completed'
    osint_job.report_file.name = str(file_path)
    osint_job.save()

    from django.urls import reverse
    url = reverse('osint-download-report', kwargs={'pk': osint_job.id})
    response = api_client.get(url)

    assert response.status_code == 200
    assert 'attachment' in response.get('Content-Disposition', '')
```

---

## Implementations

### `risk_assessor.py`

**File:** `backend/osint/services/risk_assessor.py`

```python
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass(frozen=True)
class RiskAssessment:
    finding: str
    likelihood: int
    impact: int
    score: int
    severity: RiskLevel
    remediation_phase: int  # 1=0-30d, 2=30-90d, 3=90-180d


def calculate_risk_score(likelihood: int, impact: int) -> int:
    if not (1 <= likelihood <= 5):
        raise ValueError(f"likelihood must be 1-5, got {likelihood}")
    if not (1 <= impact <= 5):
        raise ValueError(f"impact must be 1-5, got {impact}")
    return likelihood * impact


def classify_severity(score: int) -> RiskLevel:
    if score >= 15:
        return RiskLevel.CRITICAL
    if score >= 9:
        return RiskLevel.HIGH
    if score >= 4:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def assess_email_security_risk(dmarc_policy: str, spf_assessment: str) -> RiskAssessment:
    if dmarc_policy == "missing" or spf_assessment == "missing":
        likelihood, impact = 5, 4
    elif dmarc_policy == "none":
        likelihood, impact = 4, 4
    elif dmarc_policy == "quarantine":
        likelihood, impact = 2, 3
    elif dmarc_policy == "reject" and spf_assessment == "present":
        likelihood, impact = 1, 2
    else:
        likelihood, impact = 3, 3

    score = calculate_risk_score(likelihood, impact)
    return RiskAssessment(
        finding="Email Security (SPF/DMARC)",
        likelihood=likelihood,
        impact=impact,
        score=score,
        severity=classify_severity(score),
        remediation_phase=1 if score >= 15 else 2,
    )
```

### Phase 4 Node

**File:** `backend/osint/graph/nodes/phase4_analysis.py`

```python
import json
from django.conf import settings
from osint.graph.state import OsintState
from osint.models import OsintJob, InfrastructureFinding, ServiceMapping

SYNTHESIS_PROMPT = """You are a world-class cybersecurity analyst. Synthesise the following OSINT findings for {org} ({domain}) into a structured assessment.

PHASE 1 RESEARCH:
{web_research}

DNS & INFRASTRUCTURE FINDINGS:
Subdomains: {subdomains_count} discovered
Email security: {email_security}
WHOIS: {whois_summary}

USER-SUBMITTED TERMINAL OUTPUT ANALYSIS:
{terminal_analyses}

SCREENSHOT ANALYSES:
{screenshot_analyses}

Produce a comprehensive JSON assessment:
{{
    "infrastructure_map": {{
        "cloud_providers": ["string"],
        "cdn_providers": ["string"],
        "email_providers": ["string"],
        "dns_providers": ["string"],
        "data_centers": ["string"]
    }},
    "technology_stack": [
        {{
            "vendor": "string",
            "product": "string",
            "category": "Email|Identity|Security|Infrastructure|Cloud|Endpoint|Network",
            "evidence": ["source1", "source2"],
            "confidence": "high|medium|low",
            "pellera_service_relevance": ["mdr_soc|pen_test|vciso_grc|ir_retainer|infrastructure|digital_workplace|app_modernization|ai_ops|field_cto"]
        }}
    ],
    "risk_matrix": [
        {{
            "finding": "string",
            "description": "string",
            "likelihood": 1,
            "impact": 1,
            "remediation_phase": 1
        }}
    ],
    "severity_table": [
        {{
            "finding": "string",
            "severity": "critical|high|medium|low|info",
            "category": "string",
            "remediation_action": "string"
        }}
    ],
    "service_mappings": [
        {{
            "service": "mdr_soc|pen_test|vciso_grc|ir_retainer|infrastructure|digital_workplace|app_modernization|ai_ops|field_cto",
            "finding_summary": "string",
            "urgency": "immediate|short_term|strategic",
            "justification": "string"
        }}
    ]
}}

Return ONLY valid JSON."""


def phase4_analysis(state: OsintState) -> OsintState:
    """Phase 4: Synthesise all findings into infrastructure map, risk matrix, service mappings."""
    try:
        synthesis = _run_synthesis(state)
        _persist_synthesis(state['job_id'], synthesis)
        OsintJob.objects.filter(pk=state['job_id']).update(
            status='phase4_analysis',
            phase4_completed_at=__import__('django.utils', fromlist=['timezone']).timezone.now(),
        )
        return {
            **state,
            'status': 'phase4_analysis',
            'infrastructure_map': synthesis.get('infrastructure_map'),
            'technology_stack': synthesis.get('technology_stack'),
            'risk_matrix': synthesis.get('risk_matrix'),
            'severity_table': synthesis.get('severity_table'),
            'service_mappings': synthesis.get('service_mappings'),
        }
    except Exception as exc:
        OsintJob.objects.filter(pk=state['job_id']).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}


def _run_synthesis(state: OsintState) -> dict:
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    email_sec = state.get('email_security') or {}
    prompt = SYNTHESIS_PROMPT.format(
        org=state['organization_name'],
        domain=state['primary_domain'],
        web_research=json.dumps(state.get('web_research') or {})[:3000],
        subdomains_count=len(state.get('crt_sh_subdomains') or []),
        email_security=f"Grade: {email_sec.get('overall_grade', 'unknown')}, DMARC: {email_sec.get('dmarc_policy', 'unknown')}",
        whois_summary=json.dumps(state.get('whois_data') or {})[:500],
        terminal_analyses=json.dumps(state.get('terminal_submissions') or [])[:2000],
        screenshot_analyses=json.dumps(state.get('screenshot_analyses') or [])[:2000],
    )

    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    text = response.text.strip()
    if text.startswith("```"):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
    return json.loads(text)


def _persist_synthesis(job_id: str, synthesis: dict) -> None:
    for entry in synthesis.get('infrastructure_map', {}).get('cloud_providers', []):
        InfrastructureFinding.objects.create(
            osint_job_id=job_id,
            infra_type='cloud_provider',
            provider_name=entry,
            evidence='AI synthesis from Phase 1-3 findings',
            confidence=0.8,
        )
    for mapping in synthesis.get('service_mappings', []):
        ServiceMapping.objects.create(
            osint_job_id=job_id,
            service=mapping.get('service', 'field_cto'),
            finding_summary=mapping.get('finding_summary', ''),
            urgency=mapping.get('urgency', 'strategic'),
            justification=mapping.get('justification', ''),
        )
```

### Phase 5 Node

**File:** `backend/osint/graph/nodes/phase5_report.py`

```python
import json
from django.conf import settings
from osint.graph.state import OsintState
from osint.models import OsintJob, OsintReportSection

SECTION_PROMPTS = {
    'executive_summary': (
        "Write an executive summary for an OSINT security assessment of {org} ({domain}). "
        "Include: organisation overview, financial risk context using IBM/Ponemon industry breach cost data "
        "for their sector, top 3 critical findings, overall risk grade. "
        "Tone: consultative partner, not auditor. Use 'observations' not 'vulnerabilities'. "
        "Context: {context}"
    ),
    'remediation_plan': (
        "Create a phased remediation action plan for {org} based on these findings: {severity_table}. "
        "Phase 1 (0-30 days): immediate wins. Phase 2 (30-90 days): infrastructure changes. "
        "Phase 3 (90-180 days): strategic improvements. "
        "Each item: description, owner (IT/Security/Management), effort in hours, cost benchmark. "
        "Include an investment summary table with ROSI calculation."
    ),
    'security_roadmap': (
        "Create a strategic security roadmap for {org}. "
        "12-month priorities with specific initiatives and estimated investment. "
        "3-year vision covering: Zero Trust, unified SOC, TPRM, IR readiness, cloud transformation, "
        "AI-powered detection, continuous compliance, security culture."
    ),
    'entity_findings': (
        "Write detailed findings for {org} ({domain}). Include: "
        "organisation profile, attack surface inventory ({subdomains_count} subdomains found), "
        "email security analysis (SPF: {spf}, DMARC policy: {dmarc}), "
        "technology stack ({tech_count} vendors identified), regulatory exposure. "
        "All recommendations must be technically specific and actionable."
    ),
    'regulatory_landscape': (
        "Identify and analyse the regulatory compliance landscape for {org} in the {industry} sector. "
        "Map applicable regulations to the following OSINT findings: {findings_summary}. "
        "Identify specific compliance gaps revealed by the assessment."
    ),
    'engagement_proposal': (
        "Write a consultative engagement proposal mapping OSINT findings to Pellera Technologies services. "
        "Findings: {service_mappings}. "
        "For each service: scope, duration, deliverables. Framed as 'how Pellera can help'. "
        "Services available: MDR/SOC, Pen Testing/ASM, vCISO/GRC, IR Retainer, "
        "Infrastructure, Digital Workplace, Application Modernization, AI/Intelligent Operations, Field CTO."
    ),
    'methodology': (
        "Write an OSINT methodology appendix for the assessment of {org}. "
        "Describe: passive reconnaissance techniques used, certificate transparency queries, "
        "DNS analysis methods, WHOIS investigation, screenshot-based infrastructure mapping. "
        "Emphasise: all intelligence gathered using passive, legal OSINT only. "
        "No active scanning, no exploitation, no authenticated access."
    ),
}


def phase5_generate_report(state: OsintState) -> OsintState:
    """Phase 5: Generate all report sections via Gemini."""
    try:
        _generate_all_sections(state)
        OsintJob.objects.filter(pk=state['job_id']).update(status='phase5_report')
        return {**state, 'status': 'phase5_report'}
    except Exception as exc:
        OsintJob.objects.filter(pk=state['job_id']).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}


def _generate_all_sections(state: OsintState) -> None:
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    email_sec = state.get('email_security') or {}
    tech_stack = state.get('technology_stack') or []
    severity_table = state.get('severity_table') or []
    service_mappings = state.get('service_mappings') or []

    context_vars = {
        'org': state['organization_name'],
        'domain': state['primary_domain'],
        'industry': (state.get('web_research') or {}).get('industry', 'Technology'),
        'context': json.dumps(state.get('web_research') or {})[:2000],
        'severity_table': json.dumps(severity_table)[:2000],
        'subdomains_count': len(state.get('crt_sh_subdomains') or []),
        'spf': email_sec.get('spf_assessment', 'unknown'),
        'dmarc': email_sec.get('dmarc_policy', 'unknown'),
        'tech_count': len(tech_stack),
        'findings_summary': json.dumps(severity_table[:5])[:1000],
        'service_mappings': json.dumps(service_mappings)[:2000],
    }

    for section_type, prompt_template in SECTION_PROMPTS.items():
        try:
            prompt = prompt_template.format(**context_vars)
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            content = response.text.strip()

            OsintReportSection.objects.update_or_create(
                osint_job_id=state['job_id'],
                section_type=section_type,
                defaults={
                    'title': section_type.replace('_', ' ').title(),
                    'content': content,
                    'structured_data': {},
                    'order': list(SECTION_PROMPTS.keys()).index(section_type),
                },
            )
        except Exception:
            pass  # Partial failure — continue with other sections
```

### Finalize Node

**File:** `backend/osint/graph/nodes/finalize.py`

```python
from django.utils import timezone
from osint.graph.state import OsintState
from osint.models import OsintJob
from osint.report.builder import OsintReportBuilder


def finalize_osint(state: OsintState) -> OsintState:
    """Finalize: generate .docx and mark job completed."""
    try:
        job = OsintJob.objects.get(pk=state['job_id'])
        builder = OsintReportBuilder(job)
        builder.add_all_sections()
        file_path = builder.build()

        job.report_file.name = file_path
        job.status = 'completed'
        job.phase5_completed_at = timezone.now()
        job.save(update_fields=['report_file', 'status', 'phase5_completed_at', 'updated_at'])

        return {**state, 'status': 'completed', 'report_file_path': file_path}
    except Exception as exc:
        OsintJob.objects.filter(pk=state['job_id']).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}
```

### `OsintReportBuilder`

**File:** `backend/osint/report/builder.py`

```python
import os
from django.conf import settings
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from osint.models import OsintJob, OsintReportSection
from .sections.base import BaseReportSection
from .sections.cover import CoverSection
from .sections.executive_summary import ExecutiveSummarySection
from .sections.remediation import RemediationSection
from .sections.entity_findings import EntityFindingsSection
from .sections.regulatory import RegulatorySection
from .sections.engagement_proposal import EngagementProposalSection
from .sections.methodology import MethodologySection
from .sections.infrastructure_maps import InfrastructureMapsSection


class OsintReportBuilder:
    """Builds the complete OSINT .docx report."""

    def __init__(self, osint_job: OsintJob):
        self.job = osint_job
        self.document = Document()
        self._sections: list[BaseReportSection] = []
        self._apply_global_styles()

    def _apply_global_styles(self) -> None:
        """Set document-level font and style defaults."""
        style = self.document.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)

    def add_all_sections(self) -> 'OsintReportBuilder':
        db_sections = {s.section_type: s for s in
                       OsintReportSection.objects.filter(osint_job=self.job).order_by('order')}

        self._sections = [
            CoverSection(self.job, db_sections.get('cover')),
            ExecutiveSummarySection(self.job, db_sections.get('executive_summary')),
            RemediationSection(self.job, db_sections.get('remediation_plan')),
            EntityFindingsSection(self.job, db_sections.get('entity_findings')),
            RegulatorySection(self.job, db_sections.get('regulatory_landscape')),
            EngagementProposalSection(self.job, db_sections.get('engagement_proposal')),
            MethodologySection(self.job, db_sections.get('methodology')),
            InfrastructureMapsSection(self.job),
        ]
        return self

    def build(self) -> str:
        """Render all sections and write the .docx file."""
        for section in self._sections:
            section.render(self.document)

        output_path = self._get_output_path()
        self.document.save(output_path)
        return output_path

    def _get_output_path(self) -> str:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'osint_reports')
        os.makedirs(output_dir, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c == '_' else '_'
                            for c in self.job.organization_name)
        return os.path.join(output_dir, f"OSINT_{safe_name}_{str(self.job.id)[:8]}.docx")
```

**File:** `backend/osint/report/sections/base.py`

```python
from docx import Document
from osint.models import OsintJob, OsintReportSection


class BaseReportSection:
    def __init__(self, osint_job: OsintJob, db_section: OsintReportSection | None = None):
        self.job = osint_job
        self.db_section = db_section

    def render(self, document: Document) -> None:
        raise NotImplementedError
```

**File:** `backend/osint/report/sections/cover.py`

```python
from datetime import date
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from .base import BaseReportSection


class CoverSection(BaseReportSection):
    def render(self, document: Document) -> None:
        # CONFIDENTIAL header
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("CONFIDENTIAL — INTERNAL USE ONLY")
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
        run.bold = True

        document.add_paragraph()  # spacer

        # Title
        title = document.add_heading('External Attack Surface &', level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title2 = document.add_heading('Threat Intelligence Assessment', level=0)
        title2.alignment = WD_ALIGN_PARAGRAPH.CENTER

        document.add_paragraph()

        # Prospect name
        prospect_p = document.add_paragraph()
        prospect_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = prospect_p.add_run(self.job.organization_name)
        run.font.size = Pt(20)
        run.bold = True

        document.add_paragraph()

        # Metadata
        meta = document.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        meta.add_run(f"Prepared by: Pellera Technologies\n")
        meta.add_run(f"Primary Domain: {self.job.primary_domain}\n")
        meta.add_run(f"Date: {date.today().strftime('%B %d, %Y')}\n")
        meta.add_run("\nAll intelligence gathered using passive, legal OSINT only.\n"
                     "No active scanning, no exploitation, no authenticated access.")

        document.add_page_break()
```

All other section classes follow the same pattern: `__init__(job, db_section)`, `render(document)`. The `content` field from `OsintReportSection` is rendered as formatted paragraphs using `document.add_paragraph(content)`.

For `infrastructure_maps`, embed screenshots as images:
```python
# osint/report/sections/infrastructure_maps.py
from .base import BaseReportSection
from osint.models import ScreenshotUpload
from docx import Document

class InfrastructureMapsSection(BaseReportSection):
    def render(self, document: Document) -> None:
        document.add_page_break()
        document.add_heading('Appendix C: Infrastructure Maps', level=1)
        screenshots = ScreenshotUpload.objects.filter(osint_job=self.job)
        for screenshot in screenshots:
            try:
                document.add_picture(screenshot.image.path, width=__import__('docx.shared', fromlist=['Inches']).Inches(6))
                document.add_paragraph(f"{screenshot.source.title()} — {screenshot.caption}")
            except Exception:
                document.add_paragraph(f"[Screenshot not available: {screenshot.source}]")
```

---

### API Endpoints

**`GenerateReportView` and `DownloadReportView`:**

```python
class GenerateReportView(APIView):
    def post(self, request, pk):
        try:
            job = OsintJob.objects.select_for_update().get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status not in ('phase4_analysis', 'completed'):
            return Response(
                {'detail': f'Report generation requires phase4_analysis status, got {job.status}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        job.status = 'phase5_report'
        job.save(update_fields=['status', 'updated_at'])

        import threading
        t = threading.Thread(target=self._build_report_async, args=(str(job.id),), daemon=True)
        t.start()

        return Response({'detail': 'Report generation started.'}, status=http_status.HTTP_202_ACCEPTED)

    def _build_report_async(self, job_id: str) -> None:
        from osint.graph.workflow import get_graph
        graph = get_graph()
        config = {"configurable": {"thread_id": job_id}}
        graph.invoke({}, config=config)  # resumes from phase5_report if paused there, or runs finalize


class DownloadReportView(APIView):
    def get(self, request, pk):
        try:
            job = OsintJob.objects.get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'completed' or not job.report_file:
            return Response(
                {'detail': 'Report not yet available'},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        import os
        from django.http import FileResponse
        file_path = job.report_file.path
        if not os.path.exists(file_path):
            return Response({'detail': 'Report file not found on disk'}, status=http_status.HTTP_404_NOT_FOUND)

        safe_name = "".join(c if c.isalnum() or c == '_' else '_' for c in job.organization_name)
        filename = f"Pellera_OSINT_{safe_name}.docx"

        response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
```

---

## Verification

```bash
cd backend
source venv/bin/activate
pip install python-docx
pytest osint/tests/test_services/test_risk_assessor.py -v
pytest osint/tests/test_report/ -v
pytest osint/tests/test_views/test_screenshots.py -v  # includes report endpoint tests

# Full end-to-end:
# Create job → execute → submit terminal → submit screenshot → GET report status
# When completed: GET /api/osint/jobs/{id}/report/ → should download .docx
```

---

## Done When

- [ ] `pytest osint/tests/test_services/test_risk_assessor.py` passes
- [ ] `pytest osint/tests/test_report/test_builder.py` passes
- [ ] Phase 4 node persists `InfrastructureFinding` and `ServiceMapping` records
- [ ] Phase 5 node generates all `OsintReportSection` records
- [ ] `finalize_osint` creates `.docx` file in `MEDIA_ROOT/osint_reports/`
- [ ] `POST /generate-report/` triggers report generation (returns 202)
- [ ] `GET /report/` downloads `.docx` with correct `Content-Disposition` header
- [ ] All existing tests still pass (`pytest osint/`)
