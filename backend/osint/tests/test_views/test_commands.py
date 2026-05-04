import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from osint.models import OsintJob, OsintCommandRound


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_get_commands_returns_round_data(api, osint_job):
    osint_job.status = 'awaiting_terminal_output'
    osint_job.save()
    OsintCommandRound.objects.create(
        osint_job=osint_job,
        round_number=1,
        commands=['whois acme.com', 'dig acme.com MX +short'],
        rationale='These commands reveal email infrastructure.',
    )

    url = reverse('osint-commands', kwargs={'pk': osint_job.id})
    response = api.get(url)

    assert response.status_code == 200
    data = response.json()
    assert 'rounds' in data
    assert len(data['rounds']) == 1
    assert len(data['rounds'][0]['commands']) == 2
    assert data['rounds'][0]['rationale'] == 'These commands reveal email infrastructure.'


@pytest.mark.django_db
def test_get_commands_rejects_wrong_status(api, osint_job):
    osint_job.status = 'phase1_research'
    osint_job.save()

    url = reverse('osint-commands', kwargs={'pk': osint_job.id})
    response = api.get(url)
    assert response.status_code == 400


@pytest.mark.django_db
def test_get_commands_returns_404_for_unknown_job(api):
    import uuid
    url = reverse('osint-commands', kwargs={'pk': uuid.uuid4()})
    response = api.get(url)
    assert response.status_code == 404
