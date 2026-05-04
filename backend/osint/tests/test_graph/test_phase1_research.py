import pytest
from unittest.mock import patch
from osint.graph.nodes.phase1_research import phase1_web_research
from osint.graph.state import OsintState


def _base_state(job_id: str) -> dict:
    return {
        "job_id": job_id,
        "organization_name": "Acme Corp",
        "primary_domain": "acme.com",
        "additional_domains": [],
        "engagement_context": "Test engagement",
        "research_job_id": None,
        "prior_research_context": None,
        "status": "phase1_research",
        "error": "",
        "warnings": [],
        "web_research": None, "breach_history": None, "job_postings_intel": None,
        "regulatory_framework": None, "vendor_relationships": None, "leadership_intel": None,
        "crt_sh_subdomains": None, "dns_records": None, "email_security": None,
        "whois_data": None, "arin_data": None, "terminal_submissions": None,
        "screenshots": None, "screenshot_analyses": None, "infrastructure_map": None,
        "technology_stack": None, "risk_matrix": None, "severity_table": None,
        "report_sections": None, "service_mappings": None, "report_file_path": None,
    }


@pytest.mark.django_db
def test_phase1_updates_status_on_success(osint_job):
    state = _base_state(str(osint_job.id))
    mock_result = {"company_overview": "Acme Corp is a test company"}

    with patch('osint.graph.nodes.phase1_research._run_web_research', return_value=mock_result):
        result = phase1_web_research(state)

    assert result['status'] == 'phase1_complete'
    assert result['web_research'] == mock_result
    assert result['error'] == ''


@pytest.mark.django_db
def test_phase1_does_not_mutate_input_state(osint_job):
    state = _base_state(str(osint_job.id))
    original_status = state['status']
    original_web = state['web_research']

    with patch('osint.graph.nodes.phase1_research._run_web_research', return_value={}):
        result = phase1_web_research(state)

    assert state['status'] == original_status
    assert state['web_research'] is original_web
    assert result is not state


@pytest.mark.django_db
def test_phase1_handles_failure_gracefully(osint_job):
    state = _base_state(str(osint_job.id))

    with patch('osint.graph.nodes.phase1_research._run_web_research',
               side_effect=Exception("Gemini API error")):
        result = phase1_web_research(state)

    assert result['status'] == 'failed'
    assert 'Gemini API error' in result['error']
    assert result['web_research'] is None


@pytest.mark.django_db
def test_phase1_updates_db_job_status(osint_job):
    from osint.models import OsintJob
    state = _base_state(str(osint_job.id))

    with patch('osint.graph.nodes.phase1_research._run_web_research', return_value={}):
        phase1_web_research(state)

    osint_job.refresh_from_db()
    assert osint_job.status == 'phase1_complete'
