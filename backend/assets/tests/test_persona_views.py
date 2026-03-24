"""Tests for PersonaListView, PersonaDetailView, and GeneratePersonasView (AGE-21)."""
import uuid
import pytest
from unittest.mock import patch, Mock
from django.urls import reverse
from rest_framework.test import APIClient

from research.models import ResearchJob
from assets.models import Persona


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def completed_job(db):
    return ResearchJob.objects.create(
        client_name="Acme Corp",
        sales_history="Big deal",
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
def persona(db, completed_job):
    return Persona.objects.create(
        research_job=completed_job,
        name="Alex Chen",
        title="Chief Information Officer",
        department="IT",
        seniority_level="C-Suite",
    )


# ---------------------------------------------------------------------------
# PersonaListView — GET /api/assets/personas/?research_job=<id>
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPersonaListView:

    def test_returns_empty_list_when_no_personas(self, api_client, completed_job):
        url = reverse("persona-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        assert response.status_code == 200
        assert response.data == []

    def test_returns_persona_for_matching_job(self, api_client, persona, completed_job):
        url = reverse("persona-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Alex Chen"

    def test_does_not_return_persona_for_other_job(self, api_client, db, persona):
        other_job = ResearchJob.objects.create(
            client_name="Other Corp", sales_history="", status="completed", result=""
        )
        url = reverse("persona-list")
        response = api_client.get(url, {"research_job": str(other_job.id)})
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_personas_when_no_filter(self, api_client, persona, db):
        other_job = ResearchJob.objects.create(
            client_name="Other Corp", sales_history="", status="completed", result=""
        )
        Persona.objects.create(
            research_job=other_job,
            name="Sam Lee",
            title="VP Engineering",
        )
        url = reverse("persona-list")
        response = api_client.get(url)
        assert response.status_code == 200
        names = [item["name"] for item in response.data]
        assert "Alex Chen" in names
        assert "Sam Lee" in names

    def test_response_includes_expected_fields(self, api_client, persona, completed_job):
        url = reverse("persona-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        item = response.data[0]
        for field in ["id", "name", "title", "department", "seniority_level"]:
            assert field in item, f"Expected field '{field}' in persona response"


# ---------------------------------------------------------------------------
# PersonaDetailView — GET/DELETE /api/assets/personas/<pk>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPersonaDetailView:

    def test_get_existing_persona(self, api_client, persona):
        url = reverse("persona-detail", kwargs={"pk": persona.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Alex Chen"
        assert response.data["title"] == "Chief Information Officer"

    def test_get_nonexistent_persona_returns_404(self, api_client, db):
        url = reverse("persona-detail", kwargs={"pk": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_delete_persona(self, api_client, persona):
        url = reverse("persona-detail", kwargs={"pk": persona.id})
        response = api_client.delete(url)
        assert response.status_code == 204
        assert not Persona.objects.filter(pk=persona.id).exists()


# ---------------------------------------------------------------------------
# GeneratePersonasView — POST /api/assets/personas/generate/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGeneratePersonasView:

    def test_returns_404_for_missing_job(self, api_client, db):
        url = reverse("persona-generate")
        response = api_client.post(
            url, {"research_job_id": str(uuid.uuid4())}, format="json"
        )
        assert response.status_code == 404

    def test_returns_400_for_incomplete_job(self, api_client, pending_job):
        url = reverse("persona-generate")
        response = api_client.post(
            url, {"research_job_id": str(pending_job.id)}, format="json"
        )
        assert response.status_code == 400
        assert "not completed" in response.data["error"]

    def test_returns_400_for_missing_research_job_id(self, api_client, db):
        url = reverse("persona-generate")
        response = api_client.post(url, {}, format="json")
        assert response.status_code == 400

    def test_generate_calls_generator_and_returns_201(self, api_client, completed_job):
        url = reverse("persona-generate")

        mock_persona = Persona(
            research_job=completed_job,
            name="Taylor Kim",
            title="CISO",
        )
        mock_persona.save()

        mock_generator = Mock()
        mock_generator.generate_personas.return_value = [{}]
        mock_generator.create_persona_models.return_value = [mock_persona]

        # Delete so the idempotent guard doesn't short-circuit to 200
        mock_persona.delete()

        with patch("assets.views.PersonaGenerator", return_value=mock_generator):
            response = api_client.post(
                url, {"research_job_id": str(completed_job.id)}, format="json"
            )

        assert response.status_code == 201
        assert response.data[0]["name"] == "Taylor Kim"

    def test_returns_existing_personas_on_duplicate_call(self, api_client, completed_job):
        """Second call returns 200 with existing personas (idempotent guard)."""
        Persona.objects.create(
            research_job=completed_job,
            name="Existing Persona",
            title="CTO",
        )
        url = reverse("persona-generate")
        response = api_client.post(
            url, {"research_job_id": str(completed_job.id)}, format="json"
        )
        assert response.status_code == 200
        assert response.data[0]["name"] == "Existing Persona"

    def test_generator_not_called_when_personas_already_exist(self, api_client, completed_job):
        Persona.objects.create(
            research_job=completed_job,
            name="Pre-existing",
            title="VP",
        )
        url = reverse("persona-generate")
        mock_generator = Mock()

        with patch("assets.views.PersonaGenerator", return_value=mock_generator):
            api_client.post(
                url, {"research_job_id": str(completed_job.id)}, format="json"
            )

        mock_generator.generate_personas.assert_not_called()
