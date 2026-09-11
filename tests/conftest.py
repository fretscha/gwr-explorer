# pytest-django creates a PostGIS test database (test_gwr) from settings + migrations.
# No custom django_db_setup needed now there is a single writable spatial DB.

import pytest
from django.utils import translation


@pytest.fixture(autouse=True)
def _reset_language():
    # Several tests call translation.activate("fr"/"it") to exercise per-language
    # rendering (LabelService, field labels, stats). translation.activate() sets
    # thread-local state that otherwise leaks into whichever test runs next,
    # so force every test to start at the project default (German) and clear
    # activation afterwards regardless of test outcome.
    translation.activate("de")
    yield
    translation.deactivate_all()
