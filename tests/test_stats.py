import pytest
from django.core.management import call_command

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_stats_after_import():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    from src.models import Building
    from src.services.stats import StatsService

    rows = StatsService().metric("buildings_by_canton")
    assert rows and sum(r["value"] for r in rows) == Building.objects.count()
    cat = StatsService().metric("buildings_by_category")
    assert cat and cat[0]["label"] != cat[0]["key"]  # resolved German label
