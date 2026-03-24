"""Tests for WorkProduct model — nullable project FK and research_job FK (AGE-WP)."""
import uuid
import pytest
from django.contrib.contenttypes.models import ContentType

from research.models import ResearchJob
from projects.models import Project, WorkProduct


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def research_job(db):
    return ResearchJob.objects.create(
        client_name="Widget Corp",
        sales_history="",
        status="completed",
        result="Research output",
    )


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Widget Deal",
        client_name="Widget Corp",
    )


def _content_type_for_job():
    """Return the ContentType for ResearchJob (used as a stand-in generic FK target)."""
    return ContentType.objects.get_for_model(ResearchJob)


# ---------------------------------------------------------------------------
# WorkProduct — nullable project FK
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWorkProductNullableProjectFK:
    """WorkProduct.project is optional — verify null FK is accepted."""

    def test_work_product_without_project_is_valid(self, research_job):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            project=None,
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category="insight",
        )

        assert wp.pk is not None
        assert wp.project is None
        assert wp.research_job == research_job

    def test_work_product_with_project_is_valid(self, research_job, project):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            project=project,
            research_job=None,
            content_type=ct,
            object_id=research_job.id,
            category="insight",
        )

        assert wp.project == project
        assert wp.research_job is None

    def test_work_product_with_both_fks_is_valid(self, research_job, project):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            project=project,
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category="use_case",
        )

        assert wp.project == project
        assert wp.research_job == research_job

    def test_work_product_with_neither_fk_raises_integrity_error(self, research_job):
        """CheckConstraint prevents a WorkProduct with neither project nor research_job."""
        from django.db import IntegrityError
        ct = _content_type_for_job()
        with pytest.raises(IntegrityError):
            WorkProduct.objects.create(
                project=None,
                research_job=None,
                content_type=ct,
                object_id=research_job.id,
                category="other",
            )


# ---------------------------------------------------------------------------
# WorkProduct — category choices
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWorkProductCategoryChoices:
    """WorkProduct.category must be one of the defined choices."""

    @pytest.mark.parametrize("category", [
        "play",
        "persona",
        "insight",
        "one_pager",
        "case_study",
        "use_case",
        "gap",
        "other",
    ])
    def test_all_valid_categories_are_accepted(self, research_job, category):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category=category,
        )
        assert wp.category == category


# ---------------------------------------------------------------------------
# WorkProduct — cascade delete behaviour
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWorkProductCascadeDelete:
    """Verify cascade delete rules on both FKs."""

    def test_deleting_research_job_cascades_to_work_product(self, research_job):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category="insight",
        )
        wp_id = wp.id
        research_job.delete()

        assert not WorkProduct.objects.filter(id=wp_id).exists()

    def test_deleting_project_cascades_to_work_product(self, research_job, project):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            project=project,
            content_type=ct,
            object_id=research_job.id,
            category="persona",
        )
        wp_id = wp.id
        project.delete()

        assert not WorkProduct.objects.filter(id=wp_id).exists()

    def test_deleting_job_does_not_affect_project_linked_work_products(
        self, research_job, project
    ):
        ct = _content_type_for_job()
        another_job = ResearchJob.objects.create(
            client_name="Other Corp",
            status="completed",
            result="Done",
        )
        # wp_a is anchored to the project only (no research_job FK)
        wp_a = WorkProduct.objects.create(
            project=project,
            research_job=None,
            content_type=ct,
            object_id=research_job.id,
            category="insight",
        )
        # wp_b is anchored to the other job
        wp_b = WorkProduct.objects.create(
            research_job=another_job,
            content_type=ct,
            object_id=another_job.id,
            category="insight",
        )

        research_job.delete()

        # wp_a not linked to research_job, should still exist
        assert WorkProduct.objects.filter(id=wp_a.id).exists()
        # wp_b is linked to another_job, also should still exist
        assert WorkProduct.objects.filter(id=wp_b.id).exists()


# ---------------------------------------------------------------------------
# WorkProduct — defaults and meta
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWorkProductDefaults:
    """WorkProduct defaults and str representation."""

    def test_starred_defaults_to_true(self, research_job):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category="insight",
        )
        assert wp.starred is True

    def test_notes_defaults_to_empty_string(self, research_job):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category="gap",
        )
        assert wp.notes == ""

    def test_id_is_uuid(self, research_job):
        ct = _content_type_for_job()
        wp = WorkProduct.objects.create(
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category="other",
        )
        assert isinstance(wp.id, uuid.UUID)

    def test_ordering_is_newest_first(self, research_job):
        ct = _content_type_for_job()
        wp1 = WorkProduct.objects.create(
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category="insight",
        )
        wp2 = WorkProduct.objects.create(
            research_job=research_job,
            content_type=ct,
            object_id=research_job.id,
            category="gap",
        )
        qs = WorkProduct.objects.filter(research_job=research_job)
        assert qs.first().id == wp2.id
