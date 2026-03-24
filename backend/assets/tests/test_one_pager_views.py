"""Tests for OnePagerListView, OnePagerDetailView, and GenerateOnePagerView (AGE-22)."""
import uuid
import pytest
from unittest.mock import patch, Mock
from django.urls import reverse
from rest_framework.test import APIClient

from research.models import ResearchJob
from assets.models import OnePager


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def completed_job(db):
    return ResearchJob.objects.create(
        client_name="Acme Corp",
        sales_history="Enterprise deal",
        status="completed",
        result="Research output",
    )


@pytest.fixture
def pending_job(db):
    return ResearchJob.objects.create(
        client_name="Pending Corp",
        sales_history="",
        status="pending",
        result="",
    )


@pytest.fixture
def one_pager(db, completed_job):
    return OnePager.objects.create(
        research_job=completed_job,
        title="Cloud Migration One-Pager",
        headline="Modernise your infrastructure in 6 months",
        executive_summary="Acme needs cloud.",
        challenge_section="Legacy systems cost $10M/year.",
        solution_section="Azure migration with managed services.",
        benefits_section="30% cost reduction.",
    )


# ---------------------------------------------------------------------------
# OnePagerListView — GET /api/assets/one-pagers/?research_job=<id>
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOnePagerListView:

    def test_returns_empty_list_when_no_one_pagers(self, api_client, completed_job):
        url = reverse("one-pager-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        assert response.status_code == 200
        assert response.data == []

    def test_returns_one_pager_for_matching_job(self, api_client, one_pager, completed_job):
        url = reverse("one-pager-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Cloud Migration One-Pager"

    def test_does_not_return_one_pager_for_other_job(self, api_client, db, one_pager):
        other_job = ResearchJob.objects.create(
            client_name="Other Corp", sales_history="", status="completed", result=""
        )
        url = reverse("one-pager-list")
        response = api_client.get(url, {"research_job": str(other_job.id)})
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_one_pagers_when_no_filter(self, api_client, one_pager, db):
        other_job = ResearchJob.objects.create(
            client_name="Other Corp", sales_history="", status="completed", result=""
        )
        OnePager.objects.create(
            research_job=other_job,
            title="Security One-Pager",
            headline="Protect your data",
            executive_summary="Security summary.",
            challenge_section="Threat landscape.",
            solution_section="MDR solution.",
            benefits_section="Reduced MTTR.",
        )
        url = reverse("one-pager-list")
        response = api_client.get(url)
        assert response.status_code == 200
        titles = [item["title"] for item in response.data]
        assert "Cloud Migration One-Pager" in titles
        assert "Security One-Pager" in titles

    def test_response_includes_expected_fields(self, api_client, one_pager, completed_job):
        url = reverse("one-pager-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        item = response.data[0]
        for field in ["id", "title", "headline", "executive_summary", "status"]:
            assert field in item, f"Expected field '{field}' in one-pager response"


# ---------------------------------------------------------------------------
# OnePagerDetailView — GET/DELETE /api/assets/one-pagers/<pk>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOnePagerDetailView:

    def test_get_existing_one_pager(self, api_client, one_pager):
        url = reverse("one-pager-detail", kwargs={"pk": one_pager.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["title"] == "Cloud Migration One-Pager"
        assert response.data["headline"] == "Modernise your infrastructure in 6 months"

    def test_get_nonexistent_one_pager_returns_404(self, api_client, db):
        url = reverse("one-pager-detail", kwargs={"pk": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_delete_one_pager(self, api_client, one_pager):
        url = reverse("one-pager-detail", kwargs={"pk": one_pager.id})
        response = api_client.delete(url)
        assert response.status_code == 204
        assert not OnePager.objects.filter(pk=one_pager.id).exists()


# ---------------------------------------------------------------------------
# GenerateOnePagerView — POST /api/assets/one-pagers/generate/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGenerateOnePagerView:

    def test_returns_404_for_missing_job(self, api_client, db):
        url = reverse("one-pager-generate")
        response = api_client.post(
            url, {"research_job_id": str(uuid.uuid4())}, format="json"
        )
        assert response.status_code == 404

    def test_returns_400_for_incomplete_job(self, api_client, pending_job):
        url = reverse("one-pager-generate")
        response = api_client.post(
            url, {"research_job_id": str(pending_job.id)}, format="json"
        )
        assert response.status_code == 400
        assert "not completed" in response.data["error"]

    def test_returns_400_for_missing_research_job_id(self, api_client, db):
        url = reverse("one-pager-generate")
        response = api_client.post(url, {}, format="json")
        assert response.status_code == 400

    def test_generate_calls_generator_and_returns_201(self, api_client, completed_job):
        url = reverse("one-pager-generate")

        mock_pager = OnePager(
            research_job=completed_job,
            title="AI One-Pager",
            headline="AI headline",
            executive_summary="AI summary",
            challenge_section="Challenge",
            solution_section="Solution",
            benefits_section="Benefits",
        )
        mock_pager.save()

        mock_generator = Mock()
        mock_generator.generate_one_pager.return_value = {}
        mock_generator.create_one_pager_model.return_value = mock_pager

        mock_export = Mock()
        mock_export.generate_one_pager_html.return_value = None

        # Delete so no existing one-pager exists
        mock_pager.delete()

        with patch("assets.views.OnePagerGenerator", return_value=mock_generator), \
             patch("assets.views.ExportService", return_value=mock_export):
            response = api_client.post(
                url, {"research_job_id": str(completed_job.id)}, format="json"
            )

        assert response.status_code == 201
        assert response.data["title"] == "AI One-Pager"

    def test_returns_existing_one_pager_on_duplicate_call(self, api_client, completed_job):
        """Second call returns 200 with existing one-pager (idempotent guard)."""
        OnePager.objects.create(
            research_job=completed_job,
            title="Existing One-Pager",
            headline="Existing headline",
            executive_summary="Existing summary",
            challenge_section="Challenge",
            solution_section="Solution",
            benefits_section="Benefits",
        )
        url = reverse("one-pager-generate")
        response = api_client.post(
            url, {"research_job_id": str(completed_job.id)}, format="json"
        )
        assert response.status_code == 200
        assert response.data["title"] == "Existing One-Pager"

    def test_generator_not_called_when_one_pager_already_exists(self, api_client, completed_job):
        OnePager.objects.create(
            research_job=completed_job,
            title="Pre-existing",
            headline="Headline",
            executive_summary="Summary",
            challenge_section="Challenge",
            solution_section="Solution",
            benefits_section="Benefits",
        )
        url = reverse("one-pager-generate")
        mock_generator = Mock()

        with patch("assets.views.OnePagerGenerator", return_value=mock_generator):
            api_client.post(
                url, {"research_job_id": str(completed_job.id)}, format="json"
            )

        mock_generator.generate_one_pager.assert_not_called()
