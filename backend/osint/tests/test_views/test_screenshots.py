import io
import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from PIL import Image as PilImage
from osint.models import OsintJob, ScreenshotUpload


@pytest.fixture
def api():
    return APIClient()


def _make_png_buffer(name="test.png"):
    img = PilImage.new("RGB", (100, 100), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf, name


@pytest.fixture
def job_awaiting_screenshots(db):
    return OsintJob.objects.create(
        organization_name="Acme Corp",
        primary_domain="acme.com",
        status='awaiting_screenshots',
    )


@pytest.mark.django_db
def test_upload_screenshot_accepts_valid_image(api, job_awaiting_screenshots):
    buf, name = _make_png_buffer()

    with patch('osint.views.SubmitScreenshotsView._resume_graph'):
        url = reverse('osint-submit-screenshots', kwargs={'pk': job_awaiting_screenshots.id})
        response = api.post(
            url,
            data={'source': 'dnsdumpster', 'image': (buf, name, 'image/png')},
            format='multipart',
        )

    assert response.status_code == 202
    assert ScreenshotUpload.objects.filter(osint_job=job_awaiting_screenshots).count() == 1


@pytest.mark.django_db
def test_upload_rejects_wrong_status(api, osint_job):
    osint_job.status = 'phase4_analysis'
    osint_job.save()
    buf, name = _make_png_buffer()

    url = reverse('osint-submit-screenshots', kwargs={'pk': osint_job.id})
    response = api.post(
        url,
        data={'source': 'dnsdumpster', 'image': (buf, name, 'image/png')},
        format='multipart',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_rejects_non_image(api, job_awaiting_screenshots):
    fake_file = io.BytesIO(b"This is not an image, just text.")
    fake_file.seek(0)

    url = reverse('osint-submit-screenshots', kwargs={'pk': job_awaiting_screenshots.id})
    response = api.post(
        url,
        data={'source': 'dnsdumpster', 'image': (fake_file, 'notanimage.txt', 'text/plain')},
        format='multipart',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_rejects_invalid_source(api, job_awaiting_screenshots):
    buf, name = _make_png_buffer()
    url = reverse('osint-submit-screenshots', kwargs={'pk': job_awaiting_screenshots.id})
    response = api.post(
        url,
        data={'source': 'INVALID_SOURCE', 'image': (buf, name, 'image/png')},
        format='multipart',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_enforces_max_screenshot_limit(api, job_awaiting_screenshots):
    for i in range(20):
        ScreenshotUpload.objects.create(
            osint_job=job_awaiting_screenshots,
            source='shodan',
            image='fake_path.png',
        )

    buf, name = _make_png_buffer()
    url = reverse('osint-submit-screenshots', kwargs={'pk': job_awaiting_screenshots.id})
    response = api.post(
        url,
        data={'source': 'dnsdumpster', 'image': (buf, name, 'image/png')},
        format='multipart',
    )
    assert response.status_code == 400
