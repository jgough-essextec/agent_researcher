import pytest

collect_ignore = [
    "assets/tests.py",
    "ideation/tests.py",
    "memory/tests.py",
]


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up test database."""
    pass


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Clear DRF throttle cache before every test to prevent rate-limit bleed-over."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()
