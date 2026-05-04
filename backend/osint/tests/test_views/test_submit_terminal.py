import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from osint.models import OsintJob, OsintCommandRound


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def job_awaiting_terminal(db):
    job = OsintJob.objects.create(
        organization_name="Acme Corp",
        primary_domain="acme.com",
        status='awaiting_terminal_output',
    )
    OsintCommandRound.objects.create(osint_job=job, round_number=1, commands=[])
    return job


@pytest.mark.django_db
def test_submit_terminal_output_accepts_valid_payload(api, job_awaiting_terminal):
    payload = {
        "submissions": [
            {
                "command_type": "dig",
                "command_text": "dig acme.com MX +short",
                "output_text": "10 mail.acme.com.\n20 mail2.acme.com.",
            }
        ]
    }

    with patch('osint.views.SubmitTerminalOutputView._resume_graph'):
        url = reverse('osint-submit-terminal', kwargs={'pk': job_awaiting_terminal.id})
        response = api.post(url, payload, format='json')

    assert response.status_code == 202
    job_awaiting_terminal.refresh_from_db()
    assert job_awaiting_terminal.status == 'phase2_processing'


@pytest.mark.django_db
def test_submit_rejects_wrong_status(api, osint_job):
    osint_job.status = 'phase4_analysis'
    osint_job.save()

    url = reverse('osint-submit-terminal', kwargs={'pk': osint_job.id})
    response = api.post(
        url,
        {"submissions": [{"command_type": "dig", "command_text": "", "output_text": "test"}]},
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_submit_rejects_empty_submissions(api, job_awaiting_terminal):
    url = reverse('osint-submit-terminal', kwargs={'pk': job_awaiting_terminal.id})
    response = api.post(url, {"submissions": []}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_submit_accepts_any_text_as_output(api, job_awaiting_terminal):
    """Terminal output is plain text — even 'dangerous-looking' content must be accepted."""
    payload = {
        "submissions": [{
            "command_type": "other",
            "command_text": "whois acme.com",
            "output_text": "; rm -rf /tmp/test; echo this is just text in output",
        }]
    }
    with patch('osint.views.SubmitTerminalOutputView._resume_graph'):
        url = reverse('osint-submit-terminal', kwargs={'pk': job_awaiting_terminal.id})
        response = api.post(url, payload, format='json')
    assert response.status_code == 202


@pytest.mark.django_db
def test_skip_screenshots_transitions_status(api, osint_job):
    osint_job.status = 'awaiting_screenshots'
    osint_job.save()

    with patch('osint.views.SkipScreenshotsView._resume_graph'):
        url = reverse('osint-skip-screenshots', kwargs={'pk': osint_job.id})
        response = api.post(url)

    assert response.status_code == 200
    osint_job.refresh_from_db()
    assert osint_job.status == 'phase3_processing'


@pytest.mark.django_db
def test_skip_screenshots_rejects_wrong_status(api, osint_job):
    osint_job.status = 'phase1_research'
    osint_job.save()

    url = reverse('osint-skip-screenshots', kwargs={'pk': osint_job.id})
    response = api.post(url)
    assert response.status_code == 400
