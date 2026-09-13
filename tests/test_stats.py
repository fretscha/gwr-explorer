import pytest
from django.core.management import call_command
from django.utils.translation import activate

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_stats_labels_per_language():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    from gwr.models import Building
    from gwr.services.stats import StatsService

    svc = StatsService()
    rows = svc.metric("buildings_by_canton")
    assert rows and sum(r["value"] for r in rows) == Building.objects.count()
    activate("fr")
    cat_fr = svc.metric("buildings_by_category")
    activate("de")
    cat_de = svc.metric("buildings_by_category")
    # same keys, but at least one label differs between fr and de
    assert cat_fr and cat_de
    assert any(f["label"] != d["label"] for f, d in zip(cat_fr, cat_de) if f["key"] == d["key"])
