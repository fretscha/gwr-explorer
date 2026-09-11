import pytest
from django.db import connection

pytestmark = pytest.mark.django_db


def test_postgres_connection():
    assert connection.vendor == "postgresql"
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1


def test_postgis_extension_installed():
    # Created by migration 0001 (CreateExtension("postgis")) before any
    # PointField column is created.
    with connection.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension")
        exts = {row[0] for row in cur.fetchall()}
    assert "postgis" in exts
