import os
import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from osint.models import OsintJob


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_generate_report_accepts_phase4_complete(api, osint_job):
    from django.utils import timezone
    osint_job.status = 'phase4_analysis'
    osint_job.phase4_completed_at = timezone.now()
    osint_job.save()

    with patch('osint.views.GenerateReportView._build_report_async'):
        url = reverse('osint-generate-report', kwargs={'pk': osint_job.id})
        response = api.post(url)

    assert response.status_code == 202


@pytest.mark.django_db
def test_generate_report_rejects_wrong_status(api, osint_job):
    osint_job.status = 'phase1_research'
    osint_job.save()

    url = reverse('osint-generate-report', kwargs={'pk': osint_job.id})
    response = api.post(url)
    assert response.status_code == 400


@pytest.mark.django_db
def test_download_report_returns_404_if_not_complete(api, osint_job):
    osint_job.status = 'phase4_analysis'
    osint_job.save()

    url = reverse('osint-download-report', kwargs={'pk': osint_job.id})
    response = api.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_download_report_returns_file(api, osint_job, tmp_path):
    import io
    from docx import Document
    from unittest.mock import PropertyMock

    doc = Document()
    doc.add_paragraph("Test OSINT report")
    file_path = str(tmp_path / "test_report.docx")
    doc.save(file_path)

    osint_job.status = 'completed'
    # Use a relative name so Django's safe_join doesn't raise SuspiciousFileOperation
    osint_job.report_file.name = 'osint_reports/test_report.docx'
    osint_job.save()

    url = reverse('osint-download-report', kwargs={'pk': osint_job.id})
    # Patch the .path property on the FieldFile descriptor to return our tmp file path
    with patch(
        'django.db.models.fields.files.FieldFile.path',
        new_callable=PropertyMock,
        return_value=file_path,
    ):
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__ = lambda s: io.BytesIO(b"fake docx content")
                mock_open.return_value.__exit__ = lambda s, *a: None
                response = api.get(url)

    assert response.status_code == 200
    assert 'attachment' in response.get('Content-Disposition', '')
