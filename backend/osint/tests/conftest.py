import pytest
from osint.models import OsintJob


@pytest.fixture
def osint_job(db):
    return OsintJob.objects.create(
        organization_name="Acme Corp",
        primary_domain="acme.com",
    )
