import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from research.models import ResearchJob


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestResearchJobViews:
    """Tests for research job API endpoints."""

    def test_create_research_job(self, api_client):
        """Test creating a new research job."""
        url = reverse('research-create')
        data = {
            'client_name': 'Test Corp',
            'sales_history': 'Previous purchase of $50k',
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == 201
        assert response.data['client_name'] == 'Test Corp'
        assert 'id' in response.data
        assert response.data['status'] in ['pending', 'running']

    def test_create_research_job_missing_client_name(self, api_client):
        """Test creating a research job without client name fails."""
        url = reverse('research-create')
        data = {
            'sales_history': 'Previous purchase of $50k',
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == 400

    def test_get_research_job(self, api_client):
        """Test retrieving a research job."""
        job = ResearchJob.objects.create(
            client_name='Test Corp',
            sales_history='Previous purchase',
            status='completed',
            result='Research results here',
        )

        url = reverse('research-detail', kwargs={'pk': job.id})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['client_name'] == 'Test Corp'
        assert response.data['status'] == 'completed'
        assert response.data['result'] == 'Research results here'

    def test_get_nonexistent_research_job(self, api_client):
        """Test retrieving a non-existent research job."""
        import uuid
        url = reverse('research-detail', kwargs={'pk': uuid.uuid4()})
        response = api_client.get(url)

        assert response.status_code == 404
