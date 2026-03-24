"""Tests for MemoryCapture service — deduplication guard and capture logic (AGE-17)."""
import pytest
from unittest.mock import Mock, patch

from research.models import ResearchJob, ResearchReport
from memory.models import ClientProfile, MemoryEntry
from memory.services.capture import MemoryCapture


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_vector_store():
    vs = Mock()
    vs.add_document = Mock(return_value=None)
    return vs


@pytest.fixture
def completed_job(db):
    return ResearchJob.objects.create(
        client_name="Acme Corp",
        sales_history="Prior $100k deal",
        status="completed",
        result="Research done",
        vertical="technology",
    )


@pytest.fixture
def job_with_report(db, completed_job):
    """ResearchJob with a real ResearchReport attached."""
    ResearchReport.objects.create(
        research_job=completed_job,
        company_overview="Overview of Acme Corp",
        ai_footprint="Uses TensorFlow for demand forecasting",
        pain_points=["Legacy systems", "Data silos", "Manual processes"],
        talking_points=["Strong ROI", "Cloud savings", "AI acceleration"],
        opportunities=["Cloud migration", "AI transformation"],
    )
    # Refresh to populate the reverse OneToOne cache
    completed_job.refresh_from_db()
    return completed_job


# ---------------------------------------------------------------------------
# MemoryCapture.capture_from_research
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMemoryCaptureFromResearch:
    """Tests for the top-level capture_from_research method."""

    def test_creates_client_profile_on_first_capture(self, completed_job):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        result = service.capture_from_research(completed_job)

        assert result["client_profile_created"] is True
        assert ClientProfile.objects.filter(client_name="Acme Corp").exists()

    def test_updates_existing_client_profile_on_second_capture(self, completed_job):
        ClientProfile.objects.create(
            client_name="Acme Corp",
            industry="retail",
            summary="Old summary",
        )
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        result = service.capture_from_research(completed_job)

        assert result["client_profile_created"] is False
        assert ClientProfile.objects.filter(client_name="Acme Corp").count() == 1

    def test_returns_zero_entries_when_no_report(self, completed_job):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        result = service.capture_from_research(completed_job)

        # No ResearchReport exists for this job
        assert result["memory_entries_created"] == 0

    def test_capture_returns_error_list_on_exception(self, completed_job):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        with patch.object(
            service, "_capture_client_profile", side_effect=RuntimeError("DB down")
        ):
            result = service.capture_from_research(completed_job)

        assert len(result["errors"]) == 1
        assert "DB down" in result["errors"][0]

    def test_result_includes_client_profile_id(self, completed_job):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        result = service.capture_from_research(completed_job)

        assert "client_profile_id" in result
        profile = ClientProfile.objects.get(client_name="Acme Corp")
        assert result["client_profile_id"] == str(profile.id)

    def test_creates_memory_entries_when_report_present(self, job_with_report):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        result = service.capture_from_research(job_with_report)

        # 3 talking points + 2 opportunities = 5
        assert result["memory_entries_created"] == 5


# ---------------------------------------------------------------------------
# MemoryCapture._capture_insights — deduplication guard
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMemoryCaptureDeduplication:
    """Tests for the deduplication guard in _capture_insights."""

    def test_creates_memory_entries_for_talking_points(self, job_with_report):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        count = service._capture_insights(job_with_report)

        # fixture has 3 talking points + 2 opportunities
        assert count == 5
        assert MemoryEntry.objects.filter(
            source_type="research_job",
            source_id=str(job_with_report.id),
            entry_type="best_practice",
        ).count() == 3

    def test_does_not_duplicate_talking_points_on_second_run(self, job_with_report):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        first = service._capture_insights(job_with_report)
        second = service._capture_insights(job_with_report)

        assert first == 5
        assert second == 0
        assert MemoryEntry.objects.filter(
            source_type="research_job",
            source_id=str(job_with_report.id),
            entry_type="best_practice",
        ).count() == 3

    def test_does_not_duplicate_opportunities_on_second_run(self, job_with_report):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        first = service._capture_insights(job_with_report)
        second = service._capture_insights(job_with_report)

        assert first == 5
        assert second == 0
        assert MemoryEntry.objects.filter(
            source_type="research_job",
            source_id=str(job_with_report.id),
            entry_type="research_insight",
        ).count() == 2

    def test_creates_opportunity_entries_with_correct_content(self, job_with_report):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        service._capture_insights(job_with_report)

        entries = MemoryEntry.objects.filter(
            source_type="research_job",
            source_id=str(job_with_report.id),
            entry_type="research_insight",
        )
        assert entries.count() == 2
        contents = list(entries.values_list("content", flat=True))
        assert "Cloud migration" in contents
        assert "AI transformation" in contents

    def test_caps_talking_points_at_three(self, db):
        job = ResearchJob.objects.create(
            client_name="CapsTest Corp",
            status="completed",
            result="Done",
        )
        ResearchReport.objects.create(
            research_job=job,
            talking_points=["P1", "P2", "P3", "P4", "P5"],
        )
        job.refresh_from_db()
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        count = service._capture_insights(job)

        assert MemoryEntry.objects.filter(
            source_id=str(job.id), entry_type="best_practice"
        ).count() == 3

    def test_caps_opportunities_at_two(self, db):
        job = ResearchJob.objects.create(
            client_name="CapsOpps Corp",
            status="completed",
            result="Done",
        )
        ResearchReport.objects.create(
            research_job=job,
            opportunities=["O1", "O2", "O3", "O4"],
        )
        job.refresh_from_db()
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        count = service._capture_insights(job)

        assert MemoryEntry.objects.filter(
            source_id=str(job.id), entry_type="research_insight"
        ).count() == 2

    def test_returns_zero_when_report_is_missing(self, completed_job):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        # No ResearchReport created — getattr(job, 'report', None) returns None via
        # RelatedObjectDoesNotExist, which is caught by getattr's default
        count = service._capture_insights(completed_job)

        assert count == 0

    def test_vector_store_called_for_each_new_entry(self, job_with_report):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        service._capture_insights(job_with_report)

        # 3 talking points + 2 opportunities = 5 add_document calls
        assert vs.add_document.call_count == 5

    def test_vector_store_not_called_on_duplicate(self, job_with_report):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        service._capture_insights(job_with_report)
        call_count_after_first = vs.add_document.call_count

        service._capture_insights(job_with_report)
        call_count_after_second = vs.add_document.call_count

        assert call_count_after_first == 5
        assert call_count_after_second == 5  # no additional calls for duplicates

    def test_empty_talking_points_creates_no_entries(self, db):
        job = ResearchJob.objects.create(
            client_name="EmptyPoints Corp",
            status="completed",
            result="Done",
        )
        ResearchReport.objects.create(
            research_job=job,
            talking_points=[],
            opportunities=[],
        )
        job.refresh_from_db()
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        count = service._capture_insights(job)

        assert count == 0
        assert not MemoryEntry.objects.filter(source_id=str(job.id)).exists()

    def test_different_jobs_can_have_same_talking_point(self, db):
        """Same content from two different jobs should both be stored (no cross-job dedup)."""
        shared_point = "Great ROI from cloud"
        job_a = ResearchJob.objects.create(
            client_name="Corp A Dedup", status="completed", result="Done"
        )
        job_b = ResearchJob.objects.create(
            client_name="Corp B Dedup", status="completed", result="Done"
        )
        ResearchReport.objects.create(research_job=job_a, talking_points=[shared_point])
        ResearchReport.objects.create(research_job=job_b, talking_points=[shared_point])
        job_a.refresh_from_db()
        job_b.refresh_from_db()

        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        count_a = service._capture_insights(job_a)
        count_b = service._capture_insights(job_b)

        assert count_a == 1
        assert count_b == 1
        assert MemoryEntry.objects.filter(content=shared_point).count() == 2


# ---------------------------------------------------------------------------
# MemoryCapture._capture_client_profile
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCaptureClientProfile:
    """Tests for _capture_client_profile helper."""

    def test_creates_profile_with_industry_from_vertical(self, db):
        job = ResearchJob.objects.create(
            client_name="HealthCo",
            status="completed",
            result="Done",
            vertical="healthcare",
        )
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        profile, created = service._capture_client_profile(job)

        assert created is True
        assert profile.industry == "healthcare"

    def test_creates_profile_using_result_when_no_report(self, db):
        job = ResearchJob.objects.create(
            client_name="ResultCo",
            status="completed",
            result="Summary of findings for ResultCo",
        )
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        profile, _ = service._capture_client_profile(job)

        assert "Summary of findings" in profile.summary

    def test_builds_summary_from_report_fields(self, job_with_report):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        profile, _ = service._capture_client_profile(job_with_report)

        assert "Overview of Acme Corp" in profile.summary
        assert "TensorFlow" in profile.summary

    def test_vector_id_is_set_on_profile(self, completed_job):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        profile, _ = service._capture_client_profile(completed_job)

        assert profile.vector_id == f"profile_{profile.id}"


# ---------------------------------------------------------------------------
# MemoryCapture.add_sales_play
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAddSalesPlay:
    """Tests for manually adding a sales play to the knowledge base."""

    def test_creates_sales_play_in_db(self, db):
        from memory.models import SalesPlay

        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        play = service.add_sales_play(
            title="Cloud Pitch",
            play_type="pitch",
            content="Our cloud solution delivers 50% cost reduction",
            context="Use when prospect mentions cost overruns",
            industry="technology",
            vertical="saas",
        )

        assert SalesPlay.objects.filter(title="Cloud Pitch").exists()
        assert play.play_type == "pitch"
        assert play.industry == "technology"

    def test_adds_play_to_vector_store(self, db):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        play = service.add_sales_play(
            title="ROI Pitch",
            play_type="pitch",
            content="Strong ROI within 6 months",
        )

        vs.add_document.assert_called_once()
        call_args = vs.add_document.call_args
        assert call_args[0][0] == "sales_plays"
        assert call_args[0][1] == f"play_{play.id}"

    def test_play_vector_id_matches_stored(self, db):
        vs = _make_mock_vector_store()
        service = MemoryCapture(vector_store=vs)

        play = service.add_sales_play(
            title="Objection Handler",
            play_type="objection_handler",
            content="Here is how we handle that objection",
        )

        assert play.vector_id == f"play_{play.id}"
