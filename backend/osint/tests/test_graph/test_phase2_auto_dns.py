import pytest
from unittest.mock import patch, MagicMock
from osint.graph.nodes.phase2_auto_dns import phase2_auto_dns


def _base_state(job_id: str) -> dict:
    return {
        "job_id": job_id,
        "organization_name": "Acme Corp",
        "primary_domain": "acme.com",
        "additional_domains": [],
        "engagement_context": "",
        "research_job_id": None,
        "prior_research_context": None,
        "status": "phase1_complete",
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
def test_phase2_auto_transitions_status(osint_job):
    state = _base_state(str(osint_job.id))
    mock_dns = [{"domain": "acme.com", "record_type": "MX", "values": ["10 mail.acme.com."]}]
    mock_subs = [{"name_value": "mail.acme.com", "issuer_name": "Let's Encrypt"}]

    with patch('osint.graph.nodes.phase2_auto_dns._collect_crt_sh', return_value=mock_subs):
        with patch('osint.graph.nodes.phase2_auto_dns._collect_dns_records', return_value=mock_dns):
            with patch('osint.graph.nodes.phase2_auto_dns._collect_whois', return_value={}):
                with patch('osint.graph.nodes.phase2_auto_dns._assess_email', return_value=_mock_email_assessment()):
                    result = phase2_auto_dns(state)

    assert result['status'] == 'phase2_auto'
    assert result['dns_records'] == mock_dns
    assert result['crt_sh_subdomains'] == mock_subs


@pytest.mark.django_db
def test_phase2_auto_persists_to_db(osint_job):
    from osint.models import DnsFinding, SubdomainFinding, EmailSecurityAssessment
    state = _base_state(str(osint_job.id))
    mock_dns = [{"domain": "acme.com", "record_type": "MX", "values": ["10 mail.acme.com."]}]
    mock_subs = [{"name_value": "mail.acme.com", "issuer_name": "Let's Encrypt"}]

    with patch('osint.graph.nodes.phase2_auto_dns._collect_crt_sh', return_value=mock_subs):
        with patch('osint.graph.nodes.phase2_auto_dns._collect_dns_records', return_value=mock_dns):
            with patch('osint.graph.nodes.phase2_auto_dns._collect_whois', return_value={}):
                with patch('osint.graph.nodes.phase2_auto_dns._assess_email', return_value=_mock_email_assessment()):
                    phase2_auto_dns(state)

    assert DnsFinding.objects.filter(osint_job=osint_job).count() == 1
    assert SubdomainFinding.objects.filter(osint_job=osint_job).count() == 1
    assert EmailSecurityAssessment.objects.filter(osint_job=osint_job).count() == 1


@pytest.mark.django_db
def test_phase2_auto_does_not_mutate_input_state(osint_job):
    state = _base_state(str(osint_job.id))
    original = dict(state)

    with patch('osint.graph.nodes.phase2_auto_dns._collect_crt_sh', return_value=[]):
        with patch('osint.graph.nodes.phase2_auto_dns._collect_dns_records', return_value=[]):
            with patch('osint.graph.nodes.phase2_auto_dns._collect_whois', return_value={}):
                with patch('osint.graph.nodes.phase2_auto_dns._assess_email', return_value=_mock_email_assessment()):
                    result = phase2_auto_dns(state)

    assert state['status'] == original['status']
    assert result is not state


@pytest.mark.django_db
def test_phase2_auto_handles_failure(osint_job):
    state = _base_state(str(osint_job.id))

    with patch('osint.graph.nodes.phase2_auto_dns._collect_crt_sh', side_effect=Exception("network error")):
        result = phase2_auto_dns(state)

    assert result['status'] == 'failed'
    assert 'network error' in result['error']


def _mock_email_assessment():
    from osint.services.email_security import EmailSecurityResult
    return EmailSecurityResult(
        domain="acme.com",
        has_spf=True,
        spf_record="v=spf1 include:_spf.google.com ~all",
        spf_assessment="present",
        has_dmarc=True,
        dmarc_record="v=DMARC1; p=quarantine",
        dmarc_policy="quarantine",
        mx_providers=("Google Workspace",),
        overall_grade="B",
        risk_summary="Good posture",
    )
