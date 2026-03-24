"""Tests for ideation views: use cases, feasibility, plays (AGE-18, AGE-19, AGE-20)."""
import uuid
import pytest
from unittest.mock import patch, Mock
from django.urls import reverse
from rest_framework.test import APIClient

from research.models import ResearchJob
from ideation.models import UseCase, FeasibilityAssessment, RefinedPlay


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def completed_job(db):
    return ResearchJob.objects.create(
        client_name="Acme Corp",
        sales_history="Big deal pending",
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
def use_case(db, completed_job):
    return UseCase.objects.create(
        research_job=completed_job,
        title="AI Supply Chain Optimisation",
        description="Use ML to predict demand.",
        business_problem="Excess inventory costs $5M/year.",
        proposed_solution="Deploy ML forecasting pipeline.",
        priority="high",
        impact_score=0.85,
        feasibility_score=0.75,
    )


# ---------------------------------------------------------------------------
# UseCaseListView — GET /api/ideation/use-cases/?research_job=<id>
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUseCaseListView:

    def test_returns_empty_list_when_no_use_cases(self, api_client, completed_job):
        url = reverse("use-case-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        assert response.status_code == 200
        assert response.data == []

    def test_returns_use_cases_for_matching_job(self, api_client, use_case, completed_job):
        url = reverse("use-case-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["title"] == "AI Supply Chain Optimisation"

    def test_does_not_return_use_cases_for_other_job(self, api_client, db, use_case):
        other_job = ResearchJob.objects.create(
            client_name="Other Corp", sales_history="", status="completed", result=""
        )
        url = reverse("use-case-list")
        response = api_client.get(url, {"research_job": str(other_job.id)})
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_use_cases_when_no_filter(self, api_client, use_case, db, completed_job):
        other_job = ResearchJob.objects.create(
            client_name="Other Corp", sales_history="", status="completed", result=""
        )
        UseCase.objects.create(
            research_job=other_job,
            title="Second Use Case",
            description="Desc",
            business_problem="Problem",
            proposed_solution="Solution",
        )
        url = reverse("use-case-list")
        response = api_client.get(url)
        assert response.status_code == 200
        titles = [item["title"] for item in response.data]
        assert "AI Supply Chain Optimisation" in titles
        assert "Second Use Case" in titles

    def test_response_includes_expected_fields(self, api_client, use_case, completed_job):
        url = reverse("use-case-list")
        response = api_client.get(url, {"research_job": str(completed_job.id)})
        assert response.status_code == 200
        item = response.data[0]
        for field in ["id", "title", "description", "priority", "impact_score", "status"]:
            assert field in item, f"Expected field '{field}' in use case response"


# ---------------------------------------------------------------------------
# UseCaseDetailView — GET/DELETE /api/ideation/use-cases/<pk>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUseCaseDetailView:

    def test_get_existing_use_case(self, api_client, use_case):
        url = reverse("use-case-detail", kwargs={"pk": use_case.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["title"] == "AI Supply Chain Optimisation"

    def test_get_nonexistent_returns_404(self, api_client, db):
        url = reverse("use-case-detail", kwargs={"pk": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_delete_use_case(self, api_client, use_case):
        url = reverse("use-case-detail", kwargs={"pk": use_case.id})
        response = api_client.delete(url)
        assert response.status_code == 204
        assert not UseCase.objects.filter(pk=use_case.id).exists()


# ---------------------------------------------------------------------------
# GenerateUseCasesView — POST /api/ideation/use-cases/generate/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGenerateUseCasesView:

    def test_returns_404_for_missing_job(self, api_client, db):
        url = reverse("use-case-generate")
        response = api_client.post(
            url, {"research_job_id": str(uuid.uuid4())}, format="json"
        )
        assert response.status_code == 404

    def test_returns_400_for_incomplete_job(self, api_client, pending_job):
        url = reverse("use-case-generate")
        response = api_client.post(
            url, {"research_job_id": str(pending_job.id)}, format="json"
        )
        assert response.status_code == 400
        assert "not completed" in response.data["error"]

    def test_returns_400_for_missing_research_job_id(self, api_client, db):
        url = reverse("use-case-generate")
        response = api_client.post(url, {}, format="json")
        assert response.status_code == 400

    def test_generate_calls_generator_and_returns_201(self, api_client, completed_job):
        url = reverse("use-case-generate")

        mock_uc = UseCase(
            research_job=completed_job,
            title="ML Forecasting",
            description="ML pipeline",
            business_problem="Forecast demand",
            proposed_solution="Use Vertex AI",
        )
        mock_uc.save()

        mock_generator = Mock()
        mock_generator.generate_use_cases.return_value = [{}]
        mock_generator.create_use_case_models.return_value = [mock_uc]

        with patch("ideation.views.UseCaseGenerator", return_value=mock_generator):
            response = api_client.post(
                url, {"research_job_id": str(completed_job.id)}, format="json"
            )

        assert response.status_code == 201
        assert response.data[0]["title"] == "ML Forecasting"

    def test_generator_called_once_per_request(self, api_client, completed_job):
        url = reverse("use-case-generate")

        mock_uc = UseCase(
            research_job=completed_job,
            title="Test Use Case",
            description="Desc",
            business_problem="Problem",
            proposed_solution="Solution",
        )
        mock_uc.save()

        mock_generator = Mock()
        mock_generator.generate_use_cases.return_value = [{}]
        mock_generator.create_use_case_models.return_value = [mock_uc]

        with patch("ideation.views.UseCaseGenerator", return_value=mock_generator):
            api_client.post(url, {"research_job_id": str(completed_job.id)}, format="json")

        mock_generator.generate_use_cases.assert_called_once()


# ---------------------------------------------------------------------------
# AssessFeasibilityView — POST /api/ideation/use-cases/<pk>/assess/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAssessFeasibilityView:

    def test_returns_404_for_missing_use_case(self, api_client, db):
        url = reverse("use-case-assess", kwargs={"pk": uuid.uuid4()})
        response = api_client.post(url)
        assert response.status_code == 404

    def test_assess_calls_service_and_returns_200(self, api_client, use_case):
        url = reverse("use-case-assess", kwargs={"pk": use_case.id})

        mock_assessment = FeasibilityAssessment(
            use_case=use_case,
            overall_feasibility="high",
            overall_score=0.8,
        )
        mock_assessment.save()

        mock_service = Mock()
        mock_service.assess_feasibility.return_value = {}
        mock_service.create_assessment_model.return_value = mock_assessment

        with patch("ideation.views.FeasibilityService", return_value=mock_service):
            response = api_client.post(url)

        assert response.status_code == 200
        assert response.data["overall_feasibility"] == "high"
        assert response.data["overall_score"] == 0.8

    def test_service_called_with_correct_use_case(self, api_client, use_case):
        url = reverse("use-case-assess", kwargs={"pk": use_case.id})

        mock_assessment = FeasibilityAssessment(
            use_case=use_case,
            overall_feasibility="medium",
            overall_score=0.6,
        )
        mock_assessment.save()

        mock_service = Mock()
        mock_service.assess_feasibility.return_value = {}
        mock_service.create_assessment_model.return_value = mock_assessment

        with patch("ideation.views.FeasibilityService", return_value=mock_service):
            api_client.post(url)

        mock_service.assess_feasibility.assert_called_once_with(use_case)


# ---------------------------------------------------------------------------
# RefinePlayView — POST /api/ideation/use-cases/<pk>/refine/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRefinePlayView:

    def test_returns_404_for_missing_use_case(self, api_client, db):
        url = reverse("use-case-refine", kwargs={"pk": uuid.uuid4()})
        response = api_client.post(url)
        assert response.status_code == 404

    def test_refine_calls_refiner_and_returns_200(self, api_client, use_case):
        url = reverse("use-case-refine", kwargs={"pk": use_case.id})

        mock_play = RefinedPlay(
            use_case=use_case,
            title="Cloud Migration Play",
            elevator_pitch="30-sec pitch here",
            value_proposition="Cost savings of 30%",
        )
        mock_play.save()

        mock_refiner = Mock()
        mock_refiner.refine_play.return_value = {}
        mock_refiner.create_play_model.return_value = mock_play

        with patch("ideation.views.PlayRefiner", return_value=mock_refiner):
            response = api_client.post(url)

        assert response.status_code == 200
        assert response.data["title"] == "Cloud Migration Play"

    def test_refiner_called_with_correct_use_case(self, api_client, use_case):
        url = reverse("use-case-refine", kwargs={"pk": use_case.id})

        mock_play = RefinedPlay(
            use_case=use_case,
            title="Play",
            elevator_pitch="Pitch",
            value_proposition="Value",
        )
        mock_play.save()

        mock_refiner = Mock()
        mock_refiner.refine_play.return_value = {}
        mock_refiner.create_play_model.return_value = mock_play

        with patch("ideation.views.PlayRefiner", return_value=mock_refiner):
            api_client.post(url)

        mock_refiner.refine_play.assert_called_once_with(use_case)


# ---------------------------------------------------------------------------
# RefinedPlayListView / RefinedPlayDetailView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRefinedPlayListView:

    def test_returns_empty_list_when_no_plays(self, api_client, db):
        url = reverse("play-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data == []

    def test_returns_existing_plays(self, api_client, use_case):
        RefinedPlay.objects.create(
            use_case=use_case,
            title="Cloud Play",
            elevator_pitch="Short pitch",
            value_proposition="Save money",
        )
        url = reverse("play-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Cloud Play"


@pytest.mark.django_db
class TestRefinedPlayDetailView:

    def test_get_existing_play(self, api_client, use_case):
        play = RefinedPlay.objects.create(
            use_case=use_case,
            title="Security Play",
            elevator_pitch="Protect your perimeter",
            value_proposition="Reduce breach risk by 80%",
        )
        url = reverse("play-detail", kwargs={"pk": play.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["title"] == "Security Play"

    def test_get_nonexistent_play_returns_404(self, api_client, db):
        url = reverse("play-detail", kwargs={"pk": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_delete_play(self, api_client, use_case):
        play = RefinedPlay.objects.create(
            use_case=use_case,
            title="Old Play",
            elevator_pitch="Old pitch",
            value_proposition="Old value",
        )
        url = reverse("play-detail", kwargs={"pk": play.id})
        response = api_client.delete(url)
        assert response.status_code == 204
        assert not RefinedPlay.objects.filter(pk=play.id).exists()
