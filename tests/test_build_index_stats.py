import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db(databases=["default", "gwr"], transaction=True)


def test_stats_cache_canton_totals_match():
    from src.models import Building, StatsCache

    call_command("build_index", "--only", "stats")
    rows = StatsCache.objects.filter(metric="buildings_by_canton")
    assert rows.exists()
    assert sum(r.value for r in rows) == Building.objects.using("gwr").count()
    cat = StatsCache.objects.filter(metric="buildings_by_category").first()
    assert cat is not None and cat.dim_label != cat.dim_key  # labels resolved, not raw codes
