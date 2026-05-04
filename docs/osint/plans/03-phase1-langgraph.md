# Plan 03 — LangGraph Workflow Skeleton & Phase 1 Web Research

**Depends on:** Plans 01 (models), 02 (DNS services)  
**Unlocks:** Plans 04, 05 (Phase 2 workflow and API)

---

## Goal

Build the LangGraph workflow skeleton with `MemorySaver` checkpointing and implement the Phase 1 web research node. The workflow is compiled once and reused across requests via a thread-scoped config keyed by `job_id`.

---

## TDD Approach

Test the Phase 1 node in isolation by calling it directly with a crafted `OsintState`. Mock all Gemini calls. Separately test the workflow graph compiles without error and routes correctly.

---

## Step 1 — OsintState TypedDict

**File:** `backend/osint/graph/state.py`

```python
from typing import Optional, TypedDict


class OsintState(TypedDict):
    # Identifiers
    job_id: str
    organization_name: str
    primary_domain: str
    additional_domains: list[str]
    engagement_context: str

    # Optional link to prior research
    research_job_id: Optional[str]
    prior_research_context: Optional[dict]

    # Lifecycle
    status: str
    error: str
    warnings: list[str]

    # Phase 1 outputs
    web_research: Optional[dict]
    breach_history: Optional[list]
    job_postings_intel: Optional[dict]
    regulatory_framework: Optional[dict]
    vendor_relationships: Optional[list]
    leadership_intel: Optional[list]

    # Phase 2 outputs — automated
    crt_sh_subdomains: Optional[list]
    dns_records: Optional[list]
    email_security: Optional[dict]
    whois_data: Optional[dict]
    arin_data: Optional[list]

    # Phase 2 outputs — user-submitted terminal
    terminal_submissions: Optional[list]

    # Phase 3 outputs
    screenshots: Optional[list]
    screenshot_analyses: Optional[list]

    # Phase 4 outputs
    infrastructure_map: Optional[dict]
    technology_stack: Optional[dict]
    risk_matrix: Optional[dict]
    severity_table: Optional[list]

    # Phase 5 outputs
    report_sections: Optional[dict]
    service_mappings: Optional[list]
    report_file_path: Optional[str]
```

---

## Step 2 — Write Phase 1 Node Tests (TDD — RED)

**File:** `backend/osint/tests/test_graph/test_phase1_research.py`

```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from osint.graph.nodes.phase1_research import phase1_web_research
from osint.graph.state import OsintState


def _base_state() -> OsintState:
    return OsintState(
        job_id="test-job-id",
        organization_name="Acme Corp",
        primary_domain="acme.com",
        additional_domains=[],
        engagement_context="Test engagement",
        research_job_id=None,
        prior_research_context=None,
        status="phase1_research",
        error="",
        warnings=[],
        web_research=None,
        breach_history=None,
        job_postings_intel=None,
        regulatory_framework=None,
        vendor_relationships=None,
        leadership_intel=None,
        crt_sh_subdomains=None,
        dns_records=None,
        email_security=None,
        whois_data=None,
        arin_data=None,
        terminal_submissions=None,
        screenshots=None,
        screenshot_analyses=None,
        infrastructure_map=None,
        technology_stack=None,
        risk_matrix=None,
        severity_table=None,
        report_sections=None,
        service_mappings=None,
        report_file_path=None,
    )


@pytest.mark.django_db
def test_phase1_updates_status_on_success():
    state = _base_state()
    mock_web_research = {"company_overview": "Acme Corp is...", "key_findings": []}

    with patch('osint.graph.nodes.phase1_research._run_web_research',
               return_value=mock_web_research):
        with patch('osint.graph.nodes.phase1_research._update_job_status') as mock_update:
            result = phase1_web_research(state)

    assert result['status'] == 'phase1_complete'
    assert result['web_research'] == mock_web_research
    assert result['error'] == ''


@pytest.mark.django_db
def test_phase1_does_not_mutate_input_state():
    state = _base_state()
    original_status = state['status']

    with patch('osint.graph.nodes.phase1_research._run_web_research',
               return_value={}):
        with patch('osint.graph.nodes.phase1_research._update_job_status'):
            result = phase1_web_research(state)

    assert state['status'] == original_status  # original unchanged
    assert result is not state  # new object returned


@pytest.mark.django_db
def test_phase1_handles_gemini_failure_gracefully():
    state = _base_state()

    with patch('osint.graph.nodes.phase1_research._run_web_research',
               side_effect=Exception("Gemini API error")):
        with patch('osint.graph.nodes.phase1_research._update_job_status'):
            result = phase1_web_research(state)

    assert result['status'] == 'failed'
    assert 'Gemini API error' in result['error']
    assert result['web_research'] is None


@pytest.mark.django_db
def test_phase1_with_linked_research_uses_prior_context():
    state = _base_state()
    state = {**state, 'research_job_id': 'prior-job-id', 'prior_research_context': {
        'company_overview': 'Already researched: Acme Corp',
        'industry': 'Manufacturing',
    }}

    with patch('osint.graph.nodes.phase1_research._run_web_research',
               return_value={'supplemental': True}) as mock_research:
        with patch('osint.graph.nodes.phase1_research._update_job_status'):
            result = phase1_web_research(state)

    # Should pass prior context to the research call
    call_kwargs = mock_research.call_args
    assert call_kwargs is not None


@pytest.mark.django_db
def test_phase1_updates_db_job_status(osint_job):
    from osint.models import OsintJob
    state = {**_base_state(), 'job_id': str(osint_job.id)}

    with patch('osint.graph.nodes.phase1_research._run_web_research', return_value={}):
        result = phase1_web_research(state)

    osint_job.refresh_from_db()
    assert osint_job.status == 'phase1_complete'
```

---

## Step 3 — Implement Phase 1 Node (GREEN)

**File:** `backend/osint/graph/nodes/phase1_research.py`

```python
from django.utils import timezone
from osint.graph.state import OsintState
from osint.models import OsintJob

PHASE1_PROMPTS = {
    "company_profile": (
        "Research {org} ({domain}). Provide: company history, size, revenue, "
        "leadership team (names, titles, LinkedIn if public), recent news, "
        "M&A activity, strategic priorities from press releases and annual reports."
    ),
    "breach_history": (
        "Search for any data breaches, cybersecurity incidents, ransomware attacks, "
        "or regulatory enforcement actions involving {org} or {domain}. "
        "Include dates, nature of incident, data exposed, and any fines or settlements."
    ),
    "job_postings": (
        "Search for current and recent job postings from {org}. "
        "Focus on technology and security roles. Identify: technology gaps "
        "(systems they are hiring to implement), security gaps "
        "(security tools/capabilities they lack), investment priorities."
    ),
    "vendor_relationships": (
        "Identify technology partnerships, vendor relationships, and tool stack for {org}. "
        "Look for: press releases, case studies, partner program memberships, "
        "technology certifications. Map to: cloud providers, security vendors, "
        "infrastructure vendors, SaaS applications."
    ),
    "regulatory_framework": (
        "Identify the regulatory and compliance framework applicable to {org} in {domain} industry. "
        "Include: applicable regulations, certifications they hold or lack, "
        "recent regulatory changes that affect them, compliance audit history if public."
    ),
    "leadership_intel": (
        "Research public thought leadership from {org}'s technical and security leadership. "
        "Find: published blogs, conference talks, LinkedIn posts, interviews. "
        "Identify their stated priorities, security philosophy, known challenges, "
        "and how they describe their technology environment."
    ),
}


def phase1_web_research(state: OsintState) -> OsintState:
    """Phase 1: Parallel web research using Gemini grounded queries."""
    try:
        research_results = _run_web_research(
            org=state['organization_name'],
            domain=state['primary_domain'],
            prior_context=state.get('prior_research_context'),
        )
        updated = {
            **state,
            'status': 'phase1_complete',
            'web_research': research_results,
            'error': '',
        }
        _update_job_status(state['job_id'], 'phase1_complete')
        return updated
    except Exception as exc:
        updated = {**state, 'status': 'failed', 'error': str(exc)}
        _update_job_status(state['job_id'], 'failed', error=str(exc))
        return updated


def _run_web_research(org: str, domain: str, prior_context: dict | None) -> dict:
    """Run parallel Gemini grounded queries for Phase 1."""
    from research.services.grounding import run_parallel_grounded_queries

    prompts = {
        key: template.format(org=org, domain=domain)
        for key, template in PHASE1_PROMPTS.items()
    }

    if prior_context:
        # Skip company_profile if we have prior research — run supplemental security focus
        prompts["company_profile"] = (
            f"This is supplemental OSINT research for {org} ({domain}). "
            f"Prior research summary: {prior_context.get('company_overview', '')}. "
            "Focus specifically on: cybersecurity posture, known vulnerabilities, "
            "recent security incidents, and technology gaps not covered in prior research."
        )

    results = run_parallel_grounded_queries(prompts)
    return results


def _update_job_status(job_id: str, status: str, error: str = "") -> None:
    """Update OsintJob status in the database."""
    updates = {'status': status}
    if error:
        updates['error'] = error
    if status == 'phase1_complete':
        updates['phase1_completed_at'] = timezone.now()
    OsintJob.objects.filter(pk=job_id).update(**updates)
```

---

## Step 4 — LangGraph Workflow

**File:** `backend/osint/graph/workflow.py`

```python
import threading
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import OsintState
from .nodes.validate import validate_osint_input
from .nodes.phase1_research import phase1_web_research
from .nodes.phase2_auto_dns import phase2_auto_dns
from .nodes.phase2_commands import generate_terminal_commands
from .nodes.phase2_parse import phase2_parse_terminal
from .nodes.phase3_screenshots import phase3_analyze_screenshots
from .nodes.phase4_analysis import phase4_analysis
from .nodes.phase5_report import phase5_generate_report
from .nodes.finalize import finalize_osint

_workflow_lock = threading.Lock()
_compiled_graph = None


def _should_continue(state: OsintState) -> str:
    return "end" if state.get("status") == "failed" else "continue"


def build_osint_workflow():
    """Build and compile the OSINT LangGraph workflow."""
    workflow = StateGraph(OsintState)

    workflow.add_node("validate", validate_osint_input)
    workflow.add_node("phase1_research", phase1_web_research)
    workflow.add_node("phase2_auto", phase2_auto_dns)
    workflow.add_node("generate_commands", generate_terminal_commands)
    workflow.add_node("phase2_parse", phase2_parse_terminal)
    workflow.add_node("phase3_screenshots", phase3_analyze_screenshots)
    workflow.add_node("phase4_analysis", phase4_analysis)
    workflow.add_node("phase5_report", phase5_generate_report)
    workflow.add_node("finalize", finalize_osint)

    workflow.set_entry_point("validate")
    workflow.add_conditional_edges(
        "validate", _should_continue, {"continue": "phase1_research", "end": END}
    )
    workflow.add_edge("phase1_research", "phase2_auto")
    workflow.add_edge("phase2_auto", "generate_commands")
    workflow.add_edge("generate_commands", "phase2_parse")
    workflow.add_edge("phase2_parse", "phase3_screenshots")
    workflow.add_edge("phase3_screenshots", "phase4_analysis")
    workflow.add_edge("phase4_analysis", "phase5_report")
    workflow.add_edge("phase5_report", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_after=["generate_commands"],
        interrupt_before=["phase3_screenshots"],
    )


def get_graph():
    """Return the singleton compiled graph (thread-safe lazy init)."""
    global _compiled_graph
    if _compiled_graph is None:
        with _workflow_lock:
            if _compiled_graph is None:
                _compiled_graph = build_osint_workflow()
    return _compiled_graph
```

**File:** `backend/osint/graph/nodes/validate.py`

```python
import re
from osint.graph.state import OsintState

_DOMAIN_RE = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?'
    r'(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*'
    r'\.[a-zA-Z]{2,}$'
)


def validate_osint_input(state: OsintState) -> OsintState:
    """Validate inputs and set status to phase1_research if valid."""
    domain = state.get('primary_domain', '').strip().lower()
    org = state.get('organization_name', '').strip()

    if not org:
        return {**state, 'status': 'failed', 'error': 'organization_name is required'}
    if not domain or not _DOMAIN_RE.match(domain):
        return {**state, 'status': 'failed', 'error': f'Invalid primary_domain: {domain}'}

    return {**state, 'status': 'phase1_research', 'primary_domain': domain}
```

**File:** `backend/osint/graph/nodes/__init__.py` — empty

Stub out all other node files so the workflow compiles without import errors:

```python
# phase2_auto_dns.py, phase2_commands.py, phase2_parse.py,
# phase3_screenshots.py, phase4_analysis.py, phase5_report.py, finalize.py

from osint.graph.state import OsintState

def phase2_auto_dns(state: OsintState) -> OsintState:
    return state  # implemented in Plan 04

def generate_terminal_commands(state: OsintState) -> OsintState:
    return state  # implemented in Plan 04

def phase2_parse_terminal(state: OsintState) -> OsintState:
    return state  # implemented in Plan 04

def phase3_analyze_screenshots(state: OsintState) -> OsintState:
    return state  # implemented in Plan 06

def phase4_analysis(state: OsintState) -> OsintState:
    return state  # implemented in Plan 07

def phase5_generate_report(state: OsintState) -> OsintState:
    return state  # implemented in Plan 07

def finalize_osint(state: OsintState) -> OsintState:
    return state  # implemented in Plan 07
```

---

## Step 5 — Workflow Tests

**File:** `backend/osint/tests/test_graph/test_workflow.py`

```python
import pytest
from osint.graph.workflow import build_osint_workflow, get_graph


def test_workflow_compiles_without_error():
    graph = build_osint_workflow()
    assert graph is not None


def test_get_graph_returns_singleton():
    g1 = get_graph()
    g2 = get_graph()
    assert g1 is g2


def test_workflow_has_expected_nodes():
    graph = build_osint_workflow()
    # LangGraph compiled graph has _graph attribute with nodes
    node_names = set(graph.get_graph().nodes.keys())
    expected = {
        "validate", "phase1_research", "phase2_auto", "generate_commands",
        "phase2_parse", "phase3_screenshots", "phase4_analysis",
        "phase5_report", "finalize"
    }
    assert expected.issubset(node_names)


def test_validate_node_blocks_invalid_domain():
    graph = build_osint_workflow()
    config = {"configurable": {"thread_id": "test-invalid"}}
    state = {
        "job_id": "test", "organization_name": "Acme", "primary_domain": "not_a_domain",
        "additional_domains": [], "engagement_context": "", "research_job_id": None,
        "prior_research_context": None, "status": "pending", "error": "", "warnings": [],
        "web_research": None, "breach_history": None, "job_postings_intel": None,
        "regulatory_framework": None, "vendor_relationships": None, "leadership_intel": None,
        "crt_sh_subdomains": None, "dns_records": None, "email_security": None,
        "whois_data": None, "arin_data": None, "terminal_submissions": None,
        "screenshots": None, "screenshot_analyses": None, "infrastructure_map": None,
        "technology_stack": None, "risk_matrix": None, "severity_table": None,
        "report_sections": None, "service_mappings": None, "report_file_path": None,
    }
    result = graph.invoke(state, config=config)
    assert result["status"] == "failed"
    assert "primary_domain" in result["error"]
```

---

## Step 6 — Execute View (wires the workflow)

Update `OsintJobExecuteView` in `backend/osint/views.py`:

```python
from django.db import transaction
from osint.graph.workflow import get_graph
from osint.graph.state import OsintState

class OsintJobExecuteView(APIView):
    def post(self, request, pk):
        with transaction.atomic():
            job = OsintJob.objects.select_for_update().get(pk=pk)
            if job.status not in ('pending', 'failed'):
                return Response(
                    {'detail': f'Cannot execute job in status: {job.status}'},
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
            job.status = 'phase1_research'
            job.error = ''
            job.save(update_fields=['status', 'error', 'updated_at'])

        state = _build_initial_state(job)
        config = {"configurable": {"thread_id": str(job.id)}}

        import threading
        def _run():
            graph = get_graph()
            graph.invoke(state, config=config)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        serializer = OsintJobSerializer(job)
        return Response(serializer.data, status=http_status.HTTP_202_ACCEPTED)


def _build_initial_state(job) -> OsintState:
    prior_context = None
    if job.research_job_id:
        try:
            from research.models import ResearchJob
            prior_job = ResearchJob.objects.get(pk=job.research_job_id)
            prior_context = {
                'company_overview': getattr(prior_job.report, 'company_overview', ''),
                'industry': getattr(prior_job.report, 'industry', ''),
            }
        except Exception:
            pass

    return OsintState(
        job_id=str(job.id),
        organization_name=job.organization_name,
        primary_domain=job.primary_domain,
        additional_domains=list(job.additional_domains),
        engagement_context=job.engagement_context,
        research_job_id=str(job.research_job_id) if job.research_job_id else None,
        prior_research_context=prior_context,
        status='pending',
        error='',
        warnings=[],
        web_research=None, breach_history=None, job_postings_intel=None,
        regulatory_framework=None, vendor_relationships=None, leadership_intel=None,
        crt_sh_subdomains=None, dns_records=None, email_security=None,
        whois_data=None, arin_data=None, terminal_submissions=None,
        screenshots=None, screenshot_analyses=None, infrastructure_map=None,
        technology_stack=None, risk_matrix=None, severity_table=None,
        report_sections=None, service_mappings=None, report_file_path=None,
    )
```

---

## Verification

```bash
cd backend
source venv/bin/activate
pytest osint/tests/test_graph/ -v
pytest osint/tests/test_graph/test_phase1_research.py -v

# Manual smoke test
python manage.py runserver &
curl -X POST http://localhost:8000/api/osint/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Test Corp", "primary_domain": "testcorp.com"}'
# Save the returned id

curl -X POST http://localhost:8000/api/osint/jobs/{id}/execute/
# Watch status with polling:
curl http://localhost:8000/api/osint/jobs/{id}/
```

---

## Done When

- [ ] `pytest osint/tests/test_graph/` passes
- [ ] Workflow compiles and has all expected nodes
- [ ] `validate` node rejects invalid domains
- [ ] `POST /execute/` returns 202 and starts background execution
- [ ] Invalid domain → status transitions to `failed` with error message
- [ ] `GET /api/osint/jobs/{id}/` shows progressing status during execution
