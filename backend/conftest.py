import pytest

collect_ignore = [
    "assets/tests.py",
    "memory/tests.py",
]


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up test database."""
    pass
