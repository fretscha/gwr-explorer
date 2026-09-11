import pytest
from django.db import connection

pytestmark = pytest.mark.django_db


def test_postgres_connection():
    assert connection.vendor == "postgresql"
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
