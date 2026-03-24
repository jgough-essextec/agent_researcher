"""Tests for AccountPlanListView and related asset views (AGE-23)."""
import uuid
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from research.models import ResearchJob
from assets.models import AccountPlan, Persona, OnePager


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def completed_job(db):
    return ResearchJob.objects.create(
        client_name="Acme Corp",
        sales_history="Sold $100k in 2023",
        status="completed",
        result="Research complete",
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
def other_job(db):
    return ResearchJob.objects.create(
        client_name="Other Corp",
        sales_history="",
        status="completed",
        result="Other research",
    )


# ---------------------------------------------------------------------------
# AccountPlanListView — GET /api/assets/account-plans/?research_job=<id>
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAccountPlanListView:
    """Tests for GET /api/assets/account-plans/."""

    def test_returns_empty_list_when_no_plans(self, api_client, completed_job):
        url = reverse("account-plan-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})

        assert response.status_code == 200
        assert response.data == []

    def test_returns_plan_for_matching_job(self, api_client, completed_job):
        plan = AccountPlan.objects.create(
            research_job=completed_job,
            title="Acme Account Plan",
            executive_summary="Strategic account summary",
            account_overview="Overview of Acme",
        )
        url = reverse("account-plan-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert str(response.data[0]["id"]) == str(plan.id)
        assert response.data[0]["title"] == "Acme Account Plan"

    def test_does_not_return_plan_for_other_job(self, api_client, completed_job, other_job):
        AccountPlan.objects.create(
            research_job=other_job,
            title="Other Corp Plan",
            executive_summary="Other summary",
            account_overview="Other overview",
        )
        url = reverse("account-plan-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})

        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_plans_when_no_filter(self, api_client, completed_job, other_job):
        before_count = AccountPlan.objects.count()
        AccountPlan.objects.create(
            research_job=completed_job,
            title="Plan A",
            executive_summary="Summary A",
            account_overview="Overview A",
        )
        AccountPlan.objects.create(
            research_job=other_job,
            title="Plan B",
            executive_summary="Summary B",
            account_overview="Overview B",
        )
        url = reverse("account-plan-list")
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == before_count + 2

    def test_invalid_job_id_returns_empty(self, api_client):
        url = reverse("account-plan-list")
        response = api_client.get(url, {"research_job": str(uuid.uuid4())})

        assert response.status_code == 200
        assert response.data == []

    def test_response_includes_expected_fields(self, api_client, completed_job):
        AccountPlan.objects.create(
            research_job=completed_job,
            title="Full Plan",
            executive_summary="Executive summary content",
            account_overview="Account overview content",
            strategic_objectives=["Grow revenue", "Reduce churn"],
        )
        url = reverse("account-plan-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})

        plan_data = response.data[0]
        assert "id" in plan_data
        assert "research_job" in plan_data
        assert "title" in plan_data
        assert "executive_summary" in plan_data
        assert "account_overview" in plan_data
        assert "strategic_objectives" in plan_data
        assert "status" in plan_data
        assert "created_at" in plan_data


# ---------------------------------------------------------------------------
# AccountPlanDetailView — GET/PATCH/DELETE /api/assets/account-plans/<pk>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAccountPlanDetailView:
    """Tests for individual account plan detail operations."""

    def test_get_existing_plan(self, api_client, completed_job):
        plan = AccountPlan.objects.create(
            research_job=completed_job,
            title="Detail Plan",
            executive_summary="Executive summary",
            account_overview="Overview",
        )
        url = reverse("account-plan-detail", kwargs={"pk": plan.id})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["title"] == "Detail Plan"

    def test_get_nonexistent_plan_returns_404(self, api_client):
        url = reverse("account-plan-detail", kwargs={"pk": uuid.uuid4()})
        response = api_client.get(url)

        assert response.status_code == 404

    def test_delete_plan(self, api_client, completed_job):
        plan = AccountPlan.objects.create(
            research_job=completed_job,
            title="To Delete",
            executive_summary="Delete me",
            account_overview="Bye",
        )
        url = reverse("account-plan-detail", kwargs={"pk": plan.id})
        response = api_client.delete(url)

        assert response.status_code == 204
        assert not AccountPlan.objects.filter(id=plan.id).exists()


# ---------------------------------------------------------------------------
# GenerateAccountPlanView — POST /api/assets/account-plans/generate/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGenerateAccountPlanView:
    """Tests for the account plan generation endpoint."""

    def test_generate_returns_404_for_missing_job(self, api_client):
        url = reverse("account-plan-generate")
        response = api_client.post(
            url,
            {"research_job_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code == 404
        assert "not found" in response.data["error"].lower()

    def test_generate_returns_400_for_incomplete_job(self, api_client, pending_job):
        url = reverse("account-plan-generate")
        response = api_client.post(
            url,
            {"research_job_id": str(pending_job.id)},
            format="json",
        )

        assert response.status_code == 400
        assert "not completed" in response.data["error"].lower()

    def test_generate_returns_400_for_missing_research_job_id(self, api_client):
        url = reverse("account-plan-generate")
        response = api_client.post(url, {}, format="json")

        assert response.status_code == 400

    def test_generate_calls_generator_and_returns_201(self, api_client, completed_job):
        """First generation returns 201 and creates the plan."""
        url = reverse("account-plan-generate")
        from unittest.mock import patch, Mock

        mock_plan = AccountPlan(
            research_job=completed_job,
            title="Generated Plan",
            executive_summary="AI summary",
            account_overview="AI overview",
        )
        mock_plan.save()

        mock_generator = Mock()
        mock_generator.generate_account_plan.return_value = {"title": "Generated Plan"}
        mock_generator.create_account_plan_model.return_value = mock_plan

        mock_export = Mock()
        mock_export.generate_account_plan_html.return_value = None

        # Delete so the endpoint sees no existing plan and creates one fresh
        mock_plan.delete()

        with patch("assets.views.AccountPlanGenerator", return_value=mock_generator), \
             patch("assets.views.ExportService", return_value=mock_export):
            response = api_client.post(
                url,
                {"research_job_id": str(completed_job.id)},
                format="json",
            )

        assert response.status_code == 201
        assert response.data["title"] == "Generated Plan"

    def test_generate_returns_existing_plan_on_duplicate(self, api_client, completed_job):
        """Second call returns 200 with the existing plan (idempotent duplicate guard)."""
        url = reverse("account-plan-generate")
        AccountPlan.objects.create(
            research_job=completed_job,
            title="Existing Plan",
            executive_summary="Summary",
            account_overview="Overview",
        )

        response = api_client.post(
            url,
            {"research_job_id": str(completed_job.id)},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["title"] == "Existing Plan"


# ---------------------------------------------------------------------------
# PersonaListView — GET /api/assets/personas/?research_job=<id>
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPersonaListView:
    """Tests for GET /api/assets/personas/ with research_job filter."""

    def test_returns_personas_for_job(self, api_client, completed_job):
        Persona.objects.create(
            research_job=completed_job,
            name="Alice Buyer",
            title="VP Engineering",
        )
        url = reverse("persona-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Alice Buyer"

    def test_filters_personas_by_job(self, api_client, completed_job, other_job):
        Persona.objects.create(
            research_job=completed_job,
            name="Alice",
            title="VP Engineering",
        )
        Persona.objects.create(
            research_job=other_job,
            name="Bob",
            title="CTO",
        )
        url = reverse("persona-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Alice"

    def test_returns_empty_for_unknown_job(self, api_client):
        url = reverse("persona-list")
        response = api_client.get(url, {"research_job": str(uuid.uuid4())})

        assert response.status_code == 200
        assert response.data == []


# ---------------------------------------------------------------------------
# OnePagerListView — GET /api/assets/one-pagers/?research_job=<id>
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOnePagerListView:
    """Tests for GET /api/assets/one-pagers/ with research_job filter."""

    def test_returns_one_pager_for_job(self, api_client, completed_job):
        OnePager.objects.create(
            research_job=completed_job,
            title="Acme One-Pager",
            headline="Modern AI for Modern Challenges",
            executive_summary="Executive summary",
            challenge_section="Challenges",
            solution_section="Solutions",
            benefits_section="Benefits",
        )
        url = reverse("one-pager-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Acme One-Pager"

    def test_filters_one_pagers_by_job(self, api_client, completed_job, other_job):
        OnePager.objects.create(
            research_job=completed_job,
            title="Acme Pager",
            headline="H1",
            executive_summary="S1",
            challenge_section="C1",
            solution_section="Sol1",
            benefits_section="B1",
        )
        OnePager.objects.create(
            research_job=other_job,
            title="Other Pager",
            headline="H2",
            executive_summary="S2",
            challenge_section="C2",
            solution_section="Sol2",
            benefits_section="B2",
        )
        url = reverse("one-pager-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Acme Pager"
