import uuid
import pytest
from django.db import IntegrityError
from osint.models import (
    OsintJob,
    DnsFinding,
    EmailSecurityAssessment,
    OsintReportSection,
)


@pytest.mark.django_db
class TestOsintJob:
    def test_creates_with_valid_data(self):
        job = OsintJob.objects.create(
            organization_name="Acme Corp",
            primary_domain="acme.com",
        )
        assert job.pk is not None
        assert job.organization_name == "Acme Corp"
        assert job.primary_domain == "acme.com"

    def test_default_status_is_pending(self):
        job = OsintJob.objects.create(
            organization_name="Beta Ltd",
            primary_domain="beta.com",
        )
        assert job.status == "pending"

    def test_id_is_uuid(self):
        job = OsintJob.objects.create(
            organization_name="Gamma Inc",
            primary_domain="gamma.io",
        )
        # UUIDField stores a UUID object; ensure it is a valid UUID
        assert isinstance(job.id, uuid.UUID)

    def test_additional_domains_defaults_to_empty_list(self):
        job = OsintJob.objects.create(
            organization_name="Delta SA",
            primary_domain="delta.fr",
        )
        assert job.additional_domains == []

    def test_additional_domains_not_shared_between_instances(self):
        """Verify that the default=list factory creates a fresh list per instance."""
        job1 = OsintJob.objects.create(
            organization_name="Epsilon GmbH",
            primary_domain="epsilon.de",
        )
        job2 = OsintJob.objects.create(
            organization_name="Zeta BV",
            primary_domain="zeta.nl",
        )
        # Mutate job1's in-memory list and confirm job2 is unaffected
        job1.additional_domains.append("sub.epsilon.de")
        assert job2.additional_domains == []

    def test_research_job_is_nullable(self):
        job = OsintJob.objects.create(
            organization_name="Eta Corp",
            primary_domain="eta.com",
        )
        assert job.research_job is None

    def test_str_includes_organization_name_and_primary_domain(self):
        job = OsintJob.objects.create(
            organization_name="Theta Plc",
            primary_domain="theta.co.uk",
        )
        result = str(job)
        assert "Theta Plc" in result
        assert "theta.co.uk" in result


@pytest.mark.django_db
class TestDnsFinding:
    def test_creates_with_valid_data(self, osint_job):
        finding = DnsFinding.objects.create(
            osint_job=osint_job,
            domain="acme.com",
            record_type="MX",
            record_value="10 mail.acme.com",
        )
        assert finding.pk is not None
        assert finding.domain == "acme.com"
        assert finding.record_type == "MX"
        assert finding.record_value == "10 mail.acme.com"

    def test_optional_fields_default_to_blank(self, osint_job):
        finding = DnsFinding.objects.create(
            osint_job=osint_job,
            domain="acme.com",
            record_type="NS",
            record_value="ns1.acme.com",
        )
        assert finding.analysis == ""
        assert finding.risk_level == ""


@pytest.mark.django_db
class TestEmailSecurityAssessment:
    def test_has_spf_defaults_to_false(self, osint_job):
        assessment = EmailSecurityAssessment.objects.create(
            osint_job=osint_job,
            domain="acme.com",
        )
        assert assessment.has_spf is False

    def test_has_dmarc_defaults_to_false(self, osint_job):
        assessment = EmailSecurityAssessment.objects.create(
            osint_job=osint_job,
            domain="acme.com",
        )
        assert assessment.has_dmarc is False

    def test_overall_grade_defaults_to_blank(self, osint_job):
        assessment = EmailSecurityAssessment.objects.create(
            osint_job=osint_job,
            domain="acme.com",
        )
        assert assessment.overall_grade == ""


@pytest.mark.django_db
class TestOsintReportSection:
    def test_unique_together_raises_on_duplicate(self, osint_job):
        OsintReportSection.objects.create(
            osint_job=osint_job,
            section_type="cover",
            title="Cover Page",
            content="This is the cover.",
        )
        with pytest.raises(IntegrityError):
            OsintReportSection.objects.create(
                osint_job=osint_job,
                section_type="cover",
                title="Duplicate Cover",
                content="Should fail.",
            )
