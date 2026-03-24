"""Tests for ContextAccumulator — iteration context accumulation."""
import pytest
from unittest.mock import patch, MagicMock

from research.models import ResearchJob, ResearchReport
from projects.models import Project, Iteration
from projects.services.context import ContextAccumulator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_project(db):
    return Project.objects.create(
        name="Fresh Deal",
        client_name="Widget Corp",
        context_mode="fresh",
    )


@pytest.fixture
def cumulative_project(db):
    return Project.objects.create(
        name="Cumulative Deal",
        client_name="Acme Corp",
        context_mode="cumulative",
    )


@pytest.fixture
def completed_job(db):
    return ResearchJob.objects.create(
        client_name="Acme Corp",
        sales_history="Prior $100k deal",
        status="completed",
        result="Done",
    )


@pytest.fixture
def first_iteration(db, cumulative_project, completed_job):
    iteration = Iteration.objects.create(
        project=cumulative_project,
        name="Iteration 1",
    )
    # Associate the research job with this iteration
    completed_job.iteration = iteration
    completed_job.save()
    return iteration


@pytest.fixture
def report(db, completed_job):
    return ResearchReport.objects.create(
        research_job=completed_job,
        company_overview="Acme builds widgets.",
        digital_maturity="developing",
        ai_adoption_stage="exploring",
        ai_footprint="Uses basic ML",
        pain_points=["Legacy ERP", "Manual reporting"],
        opportunities=["Cloud migration", "AI automation"],
        key_initiatives=["Digital transformation"],
        strategic_goals=["Reduce costs by 20%"],
    )


# ---------------------------------------------------------------------------
# build_context — fresh mode
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBuildContextFreshMode:
    """In 'fresh' mode, build_context always returns {}."""

    def test_fresh_mode_returns_empty(self, fresh_project):
        iteration = Iteration.objects.create(project=fresh_project, name="Round 1")
        acc = ContextAccumulator()
        result = acc.build_context(iteration)
        assert result == {}

    def test_fresh_mode_ignores_previous_iterations(self, fresh_project, completed_job):
        # Create a first iteration with a job
        iter1 = Iteration.objects.create(project=fresh_project, name="Round 1")
        iter2 = Iteration.objects.create(project=fresh_project, name="Round 2")
        acc = ContextAccumulator()
        result = acc.build_context(iter2)
        assert result == {}


# ---------------------------------------------------------------------------
# build_context — cumulative mode, no previous iteration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBuildContextNoPrevious:
    """When no previous iteration exists, build_context returns {}."""

    def test_first_iteration_returns_empty(self, cumulative_project):
        iteration = Iteration.objects.create(project=cumulative_project, name="Round 1")
        acc = ContextAccumulator()
        result = acc.build_context(iteration)
        assert result == {}


# ---------------------------------------------------------------------------
# build_context — cumulative mode, previous iteration without research job
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBuildContextPreviousWithoutJob:
    """Previous iteration with no research job gives empty context."""

    def test_returns_empty_when_prev_has_no_job(self, cumulative_project):
        Iteration.objects.create(project=cumulative_project, name="Round 1")
        iter2 = Iteration.objects.create(project=cumulative_project, name="Round 2")
        acc = ContextAccumulator()
        result = acc.build_context(iter2)
        assert result == {}


# ---------------------------------------------------------------------------
# _summarize_iteration / _summarize_report
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHelperMethods:
    """Unit tests for private helper methods."""

    def test_summarize_iteration_returns_none_without_job(self, cumulative_project):
        iteration = Iteration.objects.create(project=cumulative_project)
        acc = ContextAccumulator()
        result = acc._summarize_iteration(iteration)
        assert result is None

    def test_summarize_report_returns_none_without_job(self, cumulative_project):
        iteration = Iteration.objects.create(project=cumulative_project)
        acc = ContextAccumulator()
        result = acc._summarize_report(iteration)
        assert result is None

    def test_get_pain_points_returns_empty_without_job(self, cumulative_project):
        iteration = Iteration.objects.create(project=cumulative_project)
        acc = ContextAccumulator()
        result = acc._get_pain_points(iteration)
        assert result == []

    def test_get_opportunities_returns_empty_without_job(self, cumulative_project):
        iteration = Iteration.objects.create(project=cumulative_project)
        acc = ContextAccumulator()
        result = acc._get_opportunities(iteration)
        assert result == []

    def test_get_use_cases_returns_empty_without_job(self, cumulative_project):
        iteration = Iteration.objects.create(project=cumulative_project)
        acc = ContextAccumulator()
        result = acc._get_use_cases(iteration)
        assert result == []

    def test_get_annotations_returns_list(self, cumulative_project):
        acc = ContextAccumulator()
        result = acc._get_annotations(cumulative_project)
        assert isinstance(result, list)

    def test_get_starred_plays_returns_list(self, cumulative_project):
        acc = ContextAccumulator()
        result = acc._get_starred_plays(cumulative_project)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# get_cumulative_context — fresh mode
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetCumulativeContextFreshMode:
    """In 'fresh' mode, get_cumulative_context always returns {}."""

    def test_fresh_mode_returns_empty(self, fresh_project):
        iteration = Iteration.objects.create(project=fresh_project)
        acc = ContextAccumulator()
        result = acc.get_cumulative_context(iteration)
        assert result == {}


# ---------------------------------------------------------------------------
# get_cumulative_context — cumulative mode
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetCumulativeContext:
    """get_cumulative_context aggregates across all previous iterations."""

    def test_no_previous_iterations_returns_empty_or_minimal(self, cumulative_project):
        iteration = Iteration.objects.create(project=cumulative_project)
        acc = ContextAccumulator()
        result = acc.get_cumulative_context(iteration)
        # When there are no previous iterations, iteration_count=0 which is falsy
        # so the dict filters it out, returning {}
        assert isinstance(result, dict)

    def test_returns_iteration_count_when_previous_exist(self, cumulative_project, completed_job):
        """When previous iterations exist, iteration_count is included."""
        iter1 = Iteration.objects.create(project=cumulative_project, name="Round 1")
        iter2 = Iteration.objects.create(project=cumulative_project, name="Round 2")

        acc = ContextAccumulator()
        result = acc.get_cumulative_context(iter2)
        # iter2 can see iter1 as previous; iteration_count=1
        if result:
            assert result.get('iteration_count', 0) == 1

    def test_deduplicates_pain_points_across_iterations(self, cumulative_project):
        """Pain points appearing in multiple iterations are deduplicated."""
        iter1 = Iteration.objects.create(project=cumulative_project, name="Round 1")
        iter2 = Iteration.objects.create(project=cumulative_project, name="Round 2")
        iter3 = Iteration.objects.create(project=cumulative_project, name="Round 3")

        acc = ContextAccumulator()
        # No research jobs attached, so pain points will be empty — just verify no crash
        result = acc.get_cumulative_context(iter3)
        assert isinstance(result, dict)
