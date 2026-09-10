import pytest
from django.core.management import call_command
from django.db import connections

pytestmark = pytest.mark.django_db(databases=["default", "gwr"], transaction=True)


def test_build_index_populates_fts_search():
    call_command("build_index", "--only", "search")
    with connections["default"].cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM search_entrance")
        assert cur.fetchone()[0] > 0
        cur.execute("SELECT egid FROM search_entrance WHERE search_entrance MATCH ? LIMIT 1", ("Grossholzerstrasse",))
        assert cur.fetchone() is not None
