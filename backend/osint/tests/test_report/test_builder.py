import os
import pytest
from unittest.mock import patch
from osint.report.builder import OsintReportBuilder
from osint.models import OsintReportSection


@pytest.mark.django_db
def test_builder_creates_docx_file(osint_job, tmp_path):
    OsintReportSection.objects.create(
        osint_job=osint_job,
        section_type='cover',
        title='Cover',
        content='Confidential assessment',
        order=0,
    )
    OsintReportSection.objects.create(
        osint_job=osint_job,
        section_type='executive_summary',
        title='Executive Summary',
        content='This organization has several security observations.',
        order=1,
    )

    with patch('osint.report.builder.settings') as mock_settings:
        mock_settings.MEDIA_ROOT = str(tmp_path)
        builder = OsintReportBuilder(osint_job)
        builder.add_all_sections()
        output_path = builder.build()

    assert os.path.exists(output_path)
    assert output_path.endswith('.docx')
    assert os.path.getsize(output_path) > 0


@pytest.mark.django_db
def test_builder_does_not_mutate_job(osint_job):
    original_status = osint_job.status
    with patch('osint.report.builder.settings') as mock_settings:
        import tempfile
        mock_settings.MEDIA_ROOT = tempfile.mkdtemp()
        builder = OsintReportBuilder(osint_job)
        builder.add_all_sections()
    osint_job.refresh_from_db()
    assert osint_job.status == original_status


@pytest.mark.django_db
def test_builder_output_path_contains_org_name(osint_job, tmp_path):
    with patch('osint.report.builder.settings') as mock_settings:
        mock_settings.MEDIA_ROOT = str(tmp_path)
        builder = OsintReportBuilder(osint_job)
        path = builder._get_output_path()
    assert 'Acme' in path or 'acme' in path.lower()
    assert path.endswith('.docx')
