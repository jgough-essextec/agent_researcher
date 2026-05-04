import pytest
from unittest.mock import patch
from osint.graph.nodes.phase2_commands import generate_terminal_commands


def _base_state(job_id: str) -> dict:
    return {
        "job_id": job_id,
        "organization_name": "Acme Corp",
        "primary_domain": "acme.com",
        "additional_domains": [],
        "engagement_context": "",
        "status": "phase2_auto",
        "error": "",
        "warnings": [],
        "crt_sh_subdomains": [
            {"name_value": "vpn.acme.com"},
            {"name_value": "staging.acme.com"},
        ],
        "dns_records": [
            {"domain": "acme.com", "record_type": "TXT",
             "values": ["v=spf1 include:_spf.google.com include:_spf.salesforce.com ~all"]},
        ],
        "whois_data": {"name_servers": ["ns1.cloudflare.com"]},
        "research_job_id": None, "prior_research_context": None, "web_research": None,
        "breach_history": None, "job_postings_intel": None, "regulatory_framework": None,
        "vendor_relationships": None, "leadership_intel": None, "email_security": None,
        "arin_data": None, "terminal_submissions": None, "screenshots": None,
        "screenshot_analyses": None, "infrastructure_map": None, "technology_stack": None,
        "risk_matrix": None, "severity_table": None, "report_sections": None,
        "service_mappings": None, "report_file_path": None,
    }


@pytest.mark.django_db
def test_generate_commands_creates_db_record(osint_job):
    from osint.models import OsintCommandRound
    state = _base_state(str(osint_job.id))

    result = generate_terminal_commands(state)

    assert result['status'] == 'awaiting_terminal_output'
    rounds = OsintCommandRound.objects.filter(osint_job=osint_job)
    assert rounds.exists()
    assert len(rounds.first().commands) > 0


@pytest.mark.django_db
def test_commands_contain_no_comment_lines(osint_job):
    from osint.models import OsintCommandRound
    state = _base_state(str(osint_job.id))
    generate_terminal_commands(state)

    round1 = OsintCommandRound.objects.filter(osint_job=osint_job).first()
    for cmd in round1.commands:
        assert not cmd.startswith('#'), f"Command starts with # (breaks zsh): {cmd}"


@pytest.mark.django_db
def test_commands_include_primary_domain(osint_job):
    from osint.models import OsintCommandRound
    state = _base_state(str(osint_job.id))
    generate_terminal_commands(state)

    round1 = OsintCommandRound.objects.filter(osint_job=osint_job).first()
    all_commands = " ".join(round1.commands)
    assert "acme.com" in all_commands


@pytest.mark.django_db
def test_generate_commands_does_not_mutate_state(osint_job):
    state = _base_state(str(osint_job.id))
    original_status = state['status']

    result = generate_terminal_commands(state)

    assert state['status'] == original_status
    assert result is not state
